#!/usr/bin/env python
import sys
import dxpy
import argparse
import subprocess
import time
import os
import json


argparser = argparse.ArgumentParser(description="Build the tcga mc3 variant calling pipeline on DNAnexus")
argparser.add_argument("--project", help="DNAnexus project ID", default="project-BgF714j0kF9p9BF34jZzyY2b")
argparser.add_argument("--folder", help="Folder within project (default: timestamp-based)", default=None)
argparser.add_argument("--no-applets", help="Assume applets already exist under designated folder", action="store_true")

args = argparser.parse_args()

# detect git revision
here = os.path.dirname(sys.argv[0])
git_revision = subprocess.check_output(["git", "describe", "--always", "--dirty", "--tags"]).strip()

if args.folder is None:
    args.folder = time.strftime("/%Y-%m/%d-%H%M%S-") + git_revision

project = dxpy.DXProject(args.project)
applets_folder = args.folder + "/applets"
print "project: {} ({})".format(project.name, args.project)
print "folder: {}".format(args.folder)

def build_applets():
    applets = ["fpfilter-tool", "muse-tool", "pindel-tool", "radia-tool", "samtools-pileup-tool",
               "somaticsniper-tool", "tcga-vcf-filter-tool", "varscan-tool"]

    # Build applets for assembly workflow in [args.folder]/applets/ folder
    project.new_folder(applets_folder, parents=True)
    for applet in applets:
        print "building {}...".format(applet),
        sys.stdout.flush()
        build_out = subprocess.check_output(["dx", "build", "--destination", args.project+":"+applets_folder+"/", applet])

        # take just the last line, ignore other output that makefile generates
        applet_dxid = json.loads(build_out.rstrip().split('\n')[-1])["id"]
        print applet_dxid

        applet = dxpy.DXApplet(applet_dxid, project=project.get_id())
        applet.set_properties({"git_revision": git_revision})

# helpers for name resolution
def find_applet(applet_name):
    return dxpy.find_one_data_object(classname='applet', name=applet_name,
                                     project=project.get_id(), folder=applets_folder,
                                     zero_ok=False, more_ok=False, return_handler=True)


def build_workflow():
    wf = dxpy.new_dxworkflow(title='tcga_mc3_full_run',
                              name='tcga_mc3_full_run',
                              description='TCGA mc3 variant calling pipeline',
                              project=args.project,
                              folder=args.folder,
                              properties={"git_revision": git_revision})

    # variant calling tools
    pindel_applet = find_applet("pindel-tool")
    pindel_stage_id  = wf.add_stage(pindel_applet)

    radia_applet = find_applet("radia-tool")
    radia_input = {
        "dnaNormal": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBamFile"}),
        "dnaTumor": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "fasta": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    radia_stage_id = wf.add_stage(radia_applet, stage_input=radia_input)

    somaticsniper_applet = find_applet("somaticsniper-tool")
    somaticsniper_input = {
        "normal": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBamFile"}),
        "tumor": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }

    somaticsniper_stage_id = wf.add_stage(somaticsniper_applet, stage_input=somaticsniper_input, instance_type="mem1_ssd2_x2")

    samtools_pileup_applet = find_applet("samtools-pileup-tool")
    samtools_pileup_normal_input = {
        "input1" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBamFile"}),
        "input1_index" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBaiFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    samtools_pileup_normal_stage_id = wf.add_stage(samtools_pileup_applet, stage_input=samtools_pileup_normal_input, instance_type="mem1_ssd2_x2")

    samtools_pileup_tumor_input = {
        "input1" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "input1_index" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBaiFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    samtools_pileup_tumor_stage_id = wf.add_stage(samtools_pileup_applet, stage_input=samtools_pileup_tumor_input, instance_type="mem1_ssd2_x2")

    muse_applet = find_applet("muse-tool")
    muse_input = {
        "tumor_bam" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "tumor_bai" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBaiFile"}),
        "normal_bam" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBamFile"}),
        "normal_bai" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "normalInputBaiFile"}),
        "reference" : dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"}),
        "dbsnp": dxpy.dxlink("file-Bj1V0400kF9Z3GqJY4ZbYbYj")
    }
    muse_stage_id = wf.add_stage(muse_applet, stage_input=muse_input)

    varscan_applet = find_applet("varscan-tool")
    varscan_input = {
        "normal_pileup": dxpy.dxlink({"stage": samtools_pileup_normal_stage_id, "outputField": "pileup"}),
        "tumor_pileup": dxpy.dxlink({"stage": samtools_pileup_tumor_stage_id, "outputField": "pileup"})
    }
    varscan_stage_id = wf.add_stage(varscan_applet, stage_input=varscan_input, instance_type="mem1_ssd2_x2")

    # fpfilter (somaticSniper, Varscan)
    fpfilter_applet = find_applet("fpfilter-tool")

    somatcisniper_fpfilter_input = {
        "vcf": dxpy.dxlink({"stage": somaticsniper_stage_id, "outputField": "vcf"}),
        "bam": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    somaticsniper_fpfilter_stage_id = wf.add_stage(fpfilter_applet,
                                                   stage_input=somatcisniper_fpfilter_input,
                                                   name="fpfilter-tool(somaticSniper)",
                                                   folder="fpfiltered")

    varscan_snp_fpfilter_input = {
        "vcf": dxpy.dxlink({"stage": varscan_stage_id, "outputField": "snp_vcf"}),
        "bam": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    varscan_snp_fpfilter_stage_id = wf.add_stage(fpfilter_applet,
                                                 stage_input=varscan_snp_fpfilter_input,
                                                 name="fpfilter-tool(varscan SNP)",
                                                 folder="fpfiltered")

    varscan_indel_fpfilter_input = {
        "vcf": dxpy.dxlink({"stage": varscan_stage_id, "outputField": "indel_vcf"}),
        "bam": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "tumorInputBamFile"}),
        "reference": dxpy.dxlink({"stage": pindel_stage_id, "inputField": "inputReferenceFile"})
    }
    varscan_indel_fpfilter_stage_id = wf.add_stage(fpfilter_applet,
                                                   stage_input=varscan_indel_fpfilter_input,
                                                   name="fpfilter-tool(varscan INDEL)",
                                                   folder="fpfiltered")

    # vcf_filter (All variant callers)
    vcf_filter_applet = find_applet("tcga-vcf-filter-tool")
    radia_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": radia_stage_id, "outputField": "filtered_output_vcf"}),
        "filterRejects": False
    }
    radia_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                             stage_input=radia_vcf_filter_input,
                                             name="vcffilter-tool(radia)",
                                             folder="final_filtered")

    somaticsniper_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": somaticsniper_fpfilter_stage_id, "outputField": "annotated_output"}),
        "filterRejects": False
    }
    somaticsniper_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                                     stage_input=somaticsniper_vcf_filter_input,
                                                     name="vcffilter-tool(somaticsniper)",
                                                     folder="final_filtered")

    varscan_snp_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": varscan_snp_fpfilter_stage_id, "outputField": "annotated_output"}),
        "filterRejects": True
    }
    varscan_snp_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                                   stage_input=varscan_snp_vcf_filter_input,
                                                   name="vcffilter-tool(varscan SNP)",
                                                   folder="final_filtered")

    varscan_indel_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": varscan_indel_fpfilter_stage_id, "outputField": "annotated_output"}),
        "filterRejects": True
    }
    varscan_indel_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                                     stage_input=varscan_indel_vcf_filter_input,
                                                     name="vcffilter-tool(varscan INDEL)",
                                                     folder="final_filtered")

    muse_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": muse_stage_id, "outputField": "mutations"}),
        "filterRejects": False
    }
    muse_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                            stage_input=muse_vcf_filter_input,
                                            name="vcffilter-tool(muse)",
                                            folder="final_filtered")

    pindel_vcf_filter_input = {
        "input_vcf": dxpy.dxlink({"stage": pindel_stage_id, "outputField": "outputSomaticVcf"}),
        "filterRejects": False
    }
    pindel_vcf_filter_stage_id = wf.add_stage(vcf_filter_applet,
                                              stage_input=pindel_vcf_filter_input,
                                              name="vcffilter-tool(pindel)",
                                              folder="final_filtered")
    
    vcf_reheader_applet = find_applet("tcga-vcf-reheader")
    radia_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": radia_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "radia",
        "software_version": "1",
        "software_params": "--dnaNormalMinTotalBases 4 --dnaNormalMinAltBases 2 --dnaNormalBaseQual 10 --dnaNormalMapQual 10 --dnaTumorDescription TumorDNASample --dnaTumorMinTotalBases 4 --dnaTumorMinAltBases 2 --dnaTumorBaseQual 10 --dnaTumorMapQual 10 --dnaNormalMitochon=MT --dnaTumorMitochon=MT --genotypeMinDepth 2 --genotypeMinPct 0.100",
        "center": "UCSC"
    }
    radia_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                               stage_input=radia_vcf_reheader_input,
                                               name="vcf-reheader(radia)",
                                               folder="final_reheadered")
    """
    sample_params = {
        "platform": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "platform"}),
        "participant_uuid": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "participant_uuid"}),
        "disease_code": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "disease_code"}),
        "normal_analysis_uuid": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "normal_analysis_uuid"}),
        "normal_bam_name": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "normal_bam_name"}),
        "normal_aliquot_uuid": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "normal_aliquot_id"}),
        "normal_aliquot_barcode": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "normal_aliquot_barcode"}),
        "tumor_analysis_uuid": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "tumor_analysis_uuid"}),
        "tumor_bam_name": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "tumor_bam_name"}),
        "tumor_aliquot_uuid": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "tumor_aliquot_uuid"}),
        "tumor_aliquot_barcode": dxpy.dxlink({"stage": radia_vcf_reheader_stage_id, "inputField": "tumor_aliquot_barcode"})
    }
    """
    somaticsniper_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": somaticsniper_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "somaticsniper",
        "software_version": "v1.0.5.0",
        "software_params": "-Q 40 -n NORMAL -q 1 -s 0.01 -r 0.001",
        "center": "WUSTL"
    }
    #somaticsniper_vcf_reheader_input.update(sample_params)
    somaticsniper_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                                       stage_input=somaticsniper_vcf_reheader_input,
                                                       name="vcf-reheader(somaticsniper)",
                                                       folder="final_reheadered")
    
    varscan_snp_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": varscan_snp_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "varscan",
        "software_version": "2.3.9",
        "software_params": "--output-vcf 1 --min-coverage 3 --normal-purity 1 --p-value 0.99 --min-coverage-normal 8 --min-freq-for-hom 0.75 --min-var-freq 0.08 --somatic-p-value 0.05 --min-coverage-tumor 6 --tumor-purity 1",
        "center": "WUSTL"
    }
    #varscan_snp_vcf_reheader_input.update(sample_params)
    varscan_snp_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                                     stage_input=varscan_snp_vcf_reheader_input,
                                                     name="vcf-reheader(varscan SNP)",
                                                     folder="final_reheadered")
    
    varscan_indel_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": varscan_indel_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "2.3.9",
        "software_version": "1",
        "software_params": "--output-vcf 1 --min-coverage 3 --normal-purity 1 --p-value 0.99 --min-coverage-normal 8 --min-freq-for-hom 0.75 --min-var-freq 0.08 --somatic-p-value 0.05 --min-coverage-tumor 6 --tumor-purity 1",
        "center": "WUSTL"
    }
    #varscan_indel_vcf_reheader_input.update(sample_params)
    varscan_indel_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                                       stage_input=varscan_indel_vcf_reheader_input,
                                                       name="vcf-reheader(varscan INDEL)",
                                                       folder="final_reheadered")
    
    muse_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": muse_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "muse",
        "software_version": "v1.0rc",
        "software_params": "--mode wxs",
        "center": "BCM"
    }
    #muse_vcf_reheader_input.update(sample_params)
    muse_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                             stage_input=muse_vcf_reheader_input,
                                             name="vcf-reheader(muse)",
                                             folder="final_reheadered")
    
    pindel_vcf_reheader_input = {
        "input_vcf": dxpy.dxlink({"stage": pindel_vcf_filter_stage_id, "outputField": "output_vcf"}),
        "software_name": "pindel",
        "software_version": "v0.2.5b6",
        "software_params": "--max_range_index 4 --window_size 5 --sequencing_error_rate 0.010000 --sensitivity 0.950000 --maximum_allowed_mismatch_rate 0.020000 --NM 2 --additional_mismatch 1 --min_perfect_match_around_BP 3 --min_inversion_size 50 --min_num_matched_bases 30 --balance_cutoff 0 --anchor_quality 0 --minimum_support_for_event 3 --report_long_insertions --report_duplications --report_inversions --report_breakpoints",
        "center": "WUSTL"
    }
    #pindel_vcf_reheader_input.update(sample_params)
    pindel_vcf_reheader_stage_id = wf.add_stage(vcf_reheader_applet,
                                                stage_input=pindel_vcf_reheader_input,
                                                name="vcf-reheader(pindel)",
                                                folder="final_reheadered")

    return wf

# main
if args.no_applets is not True:
    build_applets()

workflow = build_workflow()
