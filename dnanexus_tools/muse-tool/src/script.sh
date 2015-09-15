#!/bin/bash

PATH=$PATH:/opt/bin

set -e -x -o pipefail

dx-download-all-inputs --parallel

#samtools faidx "${reference_name}"

#move bai to be in same directory as bam
mv "${tumor_bai_path}" ~/in/tumor_bam/
mv "${normal_bai_path}" ~/in/normal_bam/

muse.py \
  --tumor-bam "${tumor_bam_path}" \
  --tumor-bam-index "${tumor_bai_path/tumor_bai/tumor_bam}" \
  --normal-bam "${normal_bam_path}" \
  --normal-bam-index "${normal_bai_path/normal_bai/normal_bam}" \
  -f "${reference_path}" \
  -n `nproc`

ls
mkdir -p out/mutations
sleep 100000000 
mv out.vcf "out/mutations/${tumor_bam_name%.bam}.vcf"
dx-upload-all-outputs

