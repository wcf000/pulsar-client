https://pulsar.readthedocs.io/en/latest/pulsar.cache.html#pulsar.cache.persistence.PersistenceStore.close

pulsar.cache package
Submodules
pulsar.cache.persistence module

class pulsar.cache.persistence.PersistenceStore(filename, require_sync=True)[source]

    Bases: object

    close()[source]

pulsar.cache.util module

class pulsar.cache.util.Time[source]

    Bases: object

    Time utilities of now that can be instrumented for testing.

    classmethod now()[source]

        Return the current datetime.

pulsar.cache.util.atomicish_move(source, destination, tmp_suffix='_TMP')[source]

    Move source to destination without risk of partial moves.

    > from tempfile import mkdtemp > from os.path import join, exists > temp_dir = mkdtemp() > source = join(temp_dir, “the_source”) > destination = join(temp_dir, “the_dest”) > open(source, “wb”).write(b”Hello World!”) > assert exists(source) > assert not exists(destination) > atomicish_move(source, destination) > assert not exists(source) > assert exists(destination)

Module contents

class pulsar.cache.Cache(cache_directory='file_cache')[source]
+**[Pulsar Cache]** This built-in `Cache` class manages persisted file storage in Pulsar (tiered storage), which we utilize for caching uploaded files within the broker to improve I/O efficiency.
   Maintain a cache of uploaded files.

    cache_file(local_path, ip, path)[source]

        Move a file from a temporary staging area into the cache.

    cache_required(ip, path)[source]

    destination(token)[source]

    file_available(ip, path)[source]