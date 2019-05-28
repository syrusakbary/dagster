import { execSync } from "child_process";
import { getIntrospectionQuery, buildClientSchema, printSchema } from "graphql";
import { writeFileSync } from "fs";

const result = execSync(
  `dagster-graphql -y ../../examples/dagster_examples/intro_tutorial/repository.yml '${getIntrospectionQuery(
    {
      descriptions: false
    }
  )}'`
).toString();

const schemaJson = JSON.parse(result).data;

// Write schema.graphql in the SDL format
const sdl = printSchema(buildClientSchema(schemaJson));
writeFileSync("./src/schema.graphql", sdl);

// Write filteredSchema.json, a reduced schema for runtime usage
// See https://www.apollographql.com/docs/react/advanced/fragments.html
const types = schemaJson.__schema.types.map(
  (type: { name: string; kind: string; possibleTypes: [{ name: string }] }) => {
    const { name, kind } = type;
    const possibleTypes = type.possibleTypes
      ? type.possibleTypes.map(t => ({
          name: t.name
        }))
      : null;
    return { name, kind, possibleTypes };
  }
);

writeFileSync(
  "./src/filteredSchema.generated.json",
  JSON.stringify({
    __schema: {
      types
    }
  })
);
