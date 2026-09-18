# RustFS 1.0.0 migration

The middleware Compose stack now runs `rustfs/rustfs:1.0.0` on ports 9000
(S3) and 9001 (console). RustFS stores data under `rustfs_data/`; the legacy
`minio_data/` directory is deliberately left untouched for rollback.

Existing applications may continue to use the MinIO Python/Java SDKs and the
`MINIO_*` environment variables because those clients use the S3 protocol.
New deployments can use `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, and
`S3_SECURE`; these take precedence in the Python services.

Before and after migration, verify the target with a temporary bucket:

```bash
export RUSTFS_ACCESS_KEY=minioadmin
export RUSTFS_SECRET_KEY='destination-secret'
./verify_rustfs_s3.sh
```

## Migrate existing data

Run the old MinIO instance on a temporary port, for example 19000, while
RustFS is available on 9000. Do not mount `minio_data` directly into RustFS.

```bash
export MINIO_SOURCE_ENDPOINT=http://127.0.0.1:19000
export MINIO_SOURCE_ACCESS_KEY=minioadmin
export MINIO_SOURCE_SECRET_KEY='source-secret'
export RUSTFS_DEST_ENDPOINT=http://127.0.0.1:9000
export RUSTFS_ACCESS_KEY=minioadmin
export RUSTFS_SECRET_KEY='destination-secret'

./migrate_minio_to_rustfs.sh --dry-run
./migrate_minio_to_rustfs.sh
./migrate_minio_to_rustfs.sh --verify
```

For an active system, use `--watch`, pause application writes for the final
cutover, wait for synchronization, stop the watcher, and run `--verify`.
The migration script only reads from MinIO; it does not delete source data.

## Rollback

Stop application writes, point the application endpoints back to MinIO, and
restart the affected services. Keep `minio_data/` until the RustFS retention
and backup cycle has completed successfully.
