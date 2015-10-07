#!/bin/bash

PATH=$PATH:/opt/bin

set -e -x -o pipefail

dx-download-all-inputs --parallel

mkdir -p out/output_vcf
mkdir -p out/filtered_output_vcf

mkdir radiatemp
cd radiatemp
python ~/radia.py \
  --dnaNormalFilename "${dnaNormal_path}" \
  --dnaTumorFilename "${dnaTumor_path}" \
  --fastaFilename "${fasta_path}" \
  $options \
  --outputDir ~/radiatemp/ \
  -o output.vcf \
  --scriptsDir ~/radia-1.1.5/scripts/ \
  --patientId 20c31348-e871-4abb-8ec6-5124f8d0170e \
  --number_of_procs `nproc`
mv output.vcf ~/out/output_vcf/output.radia.vcf
cd ..

mkdir radiafiltertemp
cd radiafiltertemp
python ~/radia_filter.py \
  --inputVCF ~/out/output_vcf/output.radia.vcf \
  --dnaNormalFilename "${dnaNormal_path}" \
  --dnaTumorFilename "${dnaTumor_path}" \
  --fastaFilename "${fasta_path}" \
  --outputDir ~/radiafiltertemp/ \
  -o filtered.vcf \
  --scriptsDir /home/dnanexus/radia-1.1.5/scripts/ \
  --patientId 20c31348-e871-4abb-8ec6-5124f8d0170e \
  --number_of_procs `nproc` \
  --makeTCGAcompliant \
  --filter-reject \
  --filter-germline

mv filtered.vcf ~/out/filtered_output_vcf/filtered.radia.vcf
cd ..

mkdir -p out/pass_filtered_output_vcf
egrep "^\#|PASS" ~/out/filtered_output_vcf/filtered.radia.vcf > ~/out/pass_filtered_output_vcf/pass_filtered.radia.vcf

dx-upload-all-outputs

