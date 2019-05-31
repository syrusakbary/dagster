/** This package provides a simple hello world example for reading JSON events from S3 and writing those events back to
  * S3 as parquet.
  *
  * ==Overview==
  * Note that a script is provided to simplify running this; you can invoke with:
  *
  * ./scripts/run.sh --s3-bucket "YOUR BUCKET" --s3-prefix "YOUR PREFIX" --date "2019-01-01"
  *
  * Note that Spark is expected to be a provided dependency, and you should set $SPARK_HOME to point to the location
  * of your Spark installation.
  *
  * Also you will need the following jar on your classpath (preferably placed in $SPARK_HOME/jars):
  * http://search.maven.org/remotecontent?filepath=org/apache/hadoop/hadoop-aws/2.7.1/hadoop-aws-2.7.1.jar
  *
  * Finally, you should edit $SPARK_HOME/conf/spark-defaults.conf to contain the following:
  *
  * spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
  * spark.hadoop.fs.s3a.access.key=YOUR_ACCESS_KEY
  * spark.hadoop.fs.s3a.secret.key=YOUR_SECRET_KEY
  *
  * ==References==
  * Spark + S3: http://deploymentzone.com/2015/12/20/s3a-on-spark-on-aws-ec2/
  * Spark reading from S3: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219
  *
  * ==Notes==
  * Getting AWS S3 to play nice with Spark is complicated, because it involves a dependency on both aws-java-sdk and
  * hadoop-aws, and these two libraries need to be compatible versions (and compatible with Spark) or else everything
  * explodes:
  *
  * https://hadoop.apache.org/docs/current/hadoop-aws/tools/hadoop-aws/index.html#Missing_method_in_com.amazonaws_class
  *
  * We currently use AWS 1.7.4 and hadoop-aws 2.7.1 as these are known to be compatible and work with Spark 2.4.0.
  */
package io.dagster.events

import org.apache.spark.sql.Dataset
import java.util.Date

import com.amazonaws.services.s3.AmazonS3ClientBuilder

import scala.reflect.internal.FatalError
import scala.io.Source
import models._

object EventPipeline extends SparkJob {
  final val numSampleEvents = 20

  import spark.implicits._

  def readEvents(backend: StorageBackend, date: Date): Dataset[Event] = {
    // Read event records from local path, GCS, or S3
    val records = backend match {
      case l: LocalStorageBackend => spark.read.textFile(l.inputPath)
      case g: GCSStorageBackend   => spark.read.textFile(g.inputPath)
      case s: S3StorageBackend =>
        s.getS3Objects(date)
          .toDS()
          .mapPartitions { part =>
            // S3 client objects are not serializable, so we need to instantiate each on the executors, not on the master.
            val client = AmazonS3ClientBuilder.defaultClient
            part.flatMap { key =>
              Source
                .fromInputStream(client.getObject(s.bucket, key).getObjectContent)
                .getLines

            }
          }
    }
    records.flatMap(Event.fromString)
  }

  override def run(args: Array[String]) {
    val conf = EventPipelineConfig.parse(args)

    // Must be configured for one of local, S3, or GCS only
    require(
      conf.localPath.isDefined ^
        (conf.s3Bucket.isDefined & conf.s3Prefix.isDefined) ^
        (conf.gcsInputBucket.isDefined & conf.gcsOutputBucket.isDefined),
      "Only one of (local-path), (S3 bucket/prefix), (GCS input/output buckets) may be defined"
    )

    // Create an ADT StorageBackend to abstract away which we're talking to
    val backend: StorageBackend =
      (conf.localPath, conf.s3Bucket, conf.s3Prefix, conf.gcsInputBucket, conf.gcsOutputBucket) match {
        case (_, Some(bucket), Some(prefix), _, _)            => S3StorageBackend(bucket, prefix, conf.date)
        case (Some(path), _, _, _, _)                         => LocalStorageBackend(path, conf.date)
        case (_, _, _, Some(inputBucket), Some(outputBucket)) => GCSStorageBackend(inputBucket, outputBucket, conf.date)
        case _                                                => throw new IllegalArgumentException("Error, invalid arguments")
      }

    val events = readEvents(backend, conf.date)

    // Print a few records in debug logging
    events
      .take(numSampleEvents)
      .foreach(log.debug)

    // Ensure output path is empty
    backend.ensureOutputEmpty()

    // Write event records as Parquet
    events
      .toDF()
      .write
      .parquet(backend.outputURI)
  }
}

case class EventPipelineConfig(
  s3Bucket: Option[String] = None,
  s3Prefix: Option[String] = None,
  gcsInputBucket: Option[String] = None,
  gcsOutputBucket: Option[String] = None,
  localPath: Option[String] = None,
  date: Date = new Date()
)

object EventPipelineConfig {
  val dateFormat = new java.text.SimpleDateFormat("yyyy-MM-dd")

  val parser: scopt.OptionParser[EventPipelineConfig] = new scopt.OptionParser[EventPipelineConfig]("EventPipeline") {
    opt[String]("s3-bucket")
      .action((x, c) => c.copy(s3Bucket = Some(x)))
      .text("S3 bucket to read")

    opt[String]("s3-prefix")
      .action((x, c) => c.copy(s3Prefix = Some(x)))
      .text("S3 prefix to read")

    opt[String]("gcs-input-bucket")
      .action((x, c) => c.copy(gcsInputBucket = Some(x)))
      .text("GCS input bucket to read")

    opt[String]("gcs-output-bucket")
      .action((x, c) => c.copy(gcsOutputBucket = Some(x)))
      .text("GCS output bucket to write")

    opt[String]("local-path")
      .action((x, c) => c.copy(localPath = Some(x)))
      .text("Local path prefix")

    opt[String]("date")
      .required()
      .action((x, c) => c.copy(date = dateFormat.parse(x)))
  }

  def parse(args: Array[String]): EventPipelineConfig =
    parser.parse(args, EventPipelineConfig()).getOrElse {
      throw FatalError("Incorrect options")
    }
}
