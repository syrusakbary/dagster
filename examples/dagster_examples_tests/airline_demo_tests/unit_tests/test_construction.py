def test_construct_ingest_pipeline():
    import cProfile, pstats, io

    pr = cProfile.Profile()
    pr.enable()

    from dagster_examples.airline_demo.pipelines import define_airline_demo_ingest_pipeline

    assert define_airline_demo_ingest_pipeline()

    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
