#!/bin/bash -eu

pip3 install grpcio-tools

python3 generate_proto.py

pip3 install .

pip3 install atheris pyinstaller

find "$SRC/hiero-sdk-python/.clusterfuzzlite" -name '*_fuzzer.py' -print0 | while IFS= read -r -d '' fuzzer; do
  fuzzer_basename=$(basename -s .py "$fuzzer")
  fuzzer_package="${fuzzer_basename}.pkg"

  # Bundle the fuzzer and all its dependencies into a single portable package.
  pyinstaller --distpath "$OUT" --onefile --name "$fuzzer_package" "$fuzzer"

  # Write a thin shell wrapper that ClusterFuzzLite uses to invoke the fuzzer.
  # The wrapper preloads the sanitizer library and sets ASAN_OPTIONS.
  # LD_PRELOAD is required here because the SDK uses C extensions (grpcio,
  # cryptography, protobuf) that must be covered by the sanitizer.
  cat > "$OUT/$fuzzer_basename" << EOF
#!/bin/sh
# LLVMFuzzerTestOneInput for fuzzer detection.
this_dir=\$(dirname "\$0")
LD_PRELOAD=\$this_dir/sanitizer_with_fuzzer.so \\
PYCRYPTODOME_DISABLE_DEEPBIND=1 \\
ASAN_OPTIONS=\$ASAN_OPTIONS:symbolize=1:external_symbolizer_path=\$this_dir/llvm-symbolizer:detect_leaks=0 \\
  "\$this_dir/$fuzzer_package" "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
