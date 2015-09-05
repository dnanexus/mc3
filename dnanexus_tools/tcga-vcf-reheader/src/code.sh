#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Set output file name
if [ -z "${output_vcf}"]; then
    output_vcf="${input_vcf_prefix}.reheadered.vcf"
else
    output_vcf="${output_vcf}.vcf"
fi

python ~/tcga-vcf-reheader.py "${input_vcf_path}" "${output_vcf}" "${config_yaml_path}"

ls
mkdir -p out/output_vcf
mv "${output_vcf}" "out/output_vcf/"

dx-upload-all-outputs
