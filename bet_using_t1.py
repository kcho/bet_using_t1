#!/ccnc_bin/venv/bin/python

import os
import re
import argparse
import sys
import textwrap
import pandas as pd
from nipype.interfaces import fsl
import nipype.pipeline.engine as pe

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
#pd.set_option('display.height', 1000)


def main(args):

    T1s_in_dtiDir = [x for x in os.listdir(args.dtiDir) if re.search('co2.*.nii.gz',x)]
    T1s_in_t1Dir = [x for x in os.listdir(args.t1Dir) if re.search('co2.*.nii.gz',x)]

    if T1s_in_t1Dir != []:
        pass
    else:
        if T1s_in_dtiDir != []:
            pass
        else:
            dcm_command = '/ccnc_bin/mricron/dcm2nii -o {outputDir} {inputDir}/*'.format(
                    outputDir = args.dtiDir,
                    inputDir = args.t1Dir)
            print dcm_command
            os.popen(dcm_command).read()

        
    T1_co = os.path.join(args.dtiDir,[x for x in os.listdir(args.dtiDir) if x.startswith('co2')][0])

    # bet
    t1_bet_file = os.path.join(args.dtiDir,'T1_brain.nii.gz')

    #if not os.path.isfile(t1_bet_file):
    #bet_out = t1_bet_file
    btr = pe.Node(interface = fsl.BET(), name='bet')
    btr.inputs.in_file = T1_co
    btr.inputs.frac = 0.4
    btr.inputs.center = [82, 83, 124]
    btr.inputs.mask = True
    #res = btr.run()


    # flirt
    fa_file = os.path.join(args.dtiDir,'hifi_nodif.nii.gz')
    t1_to_fa_file = os.path.join(args.dtiDir,'co_to_FA.nii.gz')
    mat_file = os.path.join(args.dtiDir,'co_to_FA')

    #if not os.path.isfile(mat_file):
    flirt = pe.Node(interface=fsl.FLIRT(), name='flirt')
    flirt.inputs.out_file = t1_to_fa_file
    flirt.inputs.reference = fa_file
    #flirt.inputs.out_matrix_file = mat_file
    flirt.inputs.cost = 'mutualinfo'
    flirt.inputs.dof = 12
    #print flirt.cmdline
    #res = flirt.run()

    # apply flirt
    #t1_mask_file = os.path.join(args.dtiDir,'T1_brain_mask.nii.gz')
    mask_from_flirt = os.path.join(args.dtiDir,'mask_from_flirt.nii.gz')

    #if not os.path.isfile(mask_from_flirt):
    flirt_apply = pe.Node(interface=fsl.FLIRT(), name='flirt_apply')
    #flirt_apply.inputs.in_file = t1_mask_file
    flirt_apply.inputs.reference = fa_file
    flirt_apply.inputs.apply_xfm = True
    flirt_apply.inputs.interp = 'nearestneighbour'
    flirt_apply.inputs.out_file = mask_from_flirt
    #print flirt_apply.cmdline
    #res = flirt.run()

    workflow = pe.Workflow(name='preproc')
    workflow.base_dir = '.'

    workflow.add_nodes([btr, flirt, flirt_apply])

    workflow.connect([
        (btr, flirt,[('out_file', 'in_file')]),
        (flirt, flirt_apply,[('out_matrix_file', 'in_matrix_file')]),
        (btr, flirt_apply,[('mask_file', 'in_file')])
            ])


    #workflow.write_graph()
    workflow.run()


    if raw_input('View ? [Y/N] : ') == 'Y':
        command = 'afni {0} {1}'.format(fa_file, mask_from_flirt)
        print command
        os.popen(command).read()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            {codeName} : Search files with user defined extensions 
            ========================================
            eg) {codeName} -e 'dcm|ima' -i /Users/kevin/NOR04_CKI
                Search dicom files in /Users/kevin/NOR04_CKI
            eg) {codeName} -c -e 'dcm|ima' -i /Users/kevin/NOR04_CKI
                Count dicom files in each directory under input 
            '''.format(codeName=os.path.basename(__file__))))
    parser.add_argument(
        '-t', '--t1Dir',
        help='T1 directory')

    parser.add_argument(
        '-d', '--dtiDir',
        help='DTI directory'
        )

    args = parser.parse_args()


    main(args)
