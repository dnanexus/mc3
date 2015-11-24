#!/bin/bash

PATH=$PATH:/opt/bin

set -e -x -o pipefail

dx-download-all-inputs --parallel

#samtools faidx "${reference_name}"
if [[ "$dbsnp" != "" ]]
then
  #tabix -p vcf "$dbsnp_path"
  gunzip "$dbsnp_path"
  dbsnp_path=${dbsnp_path%.gz}
  options="--dbsnp $dbsnp_path $options"
fi

if [[ "$cosmic" != "" ]]
then
#  gunzip $cosmic_path
#  cosmic_path=${cosmic_path%.gz}
  options="--cosmic $cosmic_path $options"
fi

#move bai to be in same directory as bam
mv "${tumor_bai_path}" ~/in/tumor_bam/
mv "${normal_bai_path}" ~/in/normal_bam/

mutect.py \
  --input_file:tumor "${tumor_bam_path}" \
  --input_file:index:tumor "${tumor_bai_path/tumor_bai/tumor_bam}" \
  --input_file:normal "${normal_bam_path}" \
  --input_file:index:normal "${normal_bai_path/normal_bai/normal_bam}" \
  --reference-sequence "${reference_path}" \
  $options \
  --vcf out.vcf \
  --ncpus `nproc`

ls
mkdir -p out/mutations
mv out.vcf "out/mutations/${tumor_bam_name%.bam}.mutect.vcf"
dx-upload-all-outputs
