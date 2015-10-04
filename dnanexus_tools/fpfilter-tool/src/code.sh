#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

if [ -z "${output}" ]; then
    output="${vcf_prefix}.filtered.vcf"
else
    output="${output}.vcf"
fi

samtools index "${bam_path}"

# Call to fpfilter
perl ~/fpfilter.pl \
    --vcf-file "${vcf_path}" \
    --bam-file "${bam_path}" \
    --bam-index "${bam_path}.bai" \
    --sample "${sample}" \
    --reference "${reference_path}" \
    --output "${output}" \
    --min-read-pos "${min_read_pos}" \
    --min-var-freq "${min_var_freq}" \
    --min-var-count "${min_var_count}" \
    --min-strandedness "${min_strandness}" \
    --max-mm-qualsum-diff "${max_mm_qualsum_diff}" \
    --max_var_mm_qualsum "${max_var_mm_qualsum}" \
    --max-mapqual-diff "${max_mapqual_diff}" \
    --max-readlen-diff "${max_readlen_diff}" \
    --min-var-dist-3 "${min_var_dist_3}"


ls
mkdir -p out/output

mv "${output}" "out/output/"

dx-upload-all-outputs
