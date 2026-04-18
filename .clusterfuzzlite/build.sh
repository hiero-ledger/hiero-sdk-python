#!/bin/bash -eu

PROJECT_DIR="$SRC/hiero-sdk-python"

cd "$PROJECT_DIR"

python3 -m pip install --upgrade pip
pip3 install grpcio-tools
python3 generate_proto.py
pip3 install .
pip3 install atheris pyinstaller

for fuzzer in "$PROJECT_DIR"/.clusterfuzzlite/*_fuzzer.py; do
  fuzzer_basename=$(basename -s .py "$fuzzer")
  fuzzer_package="${fuzzer_basename}.pkg"

  pyinstaller \
    --distpath "$OUT" \
    --workpath /tmp/pyinstaller-work \
    --specpath /tmp/pyinstaller-spec \
    --onefile \
    --name "$fuzzer_package" \
    "$fuzzer"

  cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
# LLVMFuzzerTestOneInput for fuzzer detection.
this_dir=\$(dirname "\$0")
"\$this_dir/$fuzzer_package" "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
