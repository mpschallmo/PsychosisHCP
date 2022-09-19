function output = mps_MRS_tissue_correction(options)
% usage: output = mps_MRS_tissue_correction(options)
%
% options = structure with fields (defaults set if not provided):
%     - top_dir - string, directory path to MRS data
%     - scripts_path - string, directory path to scripts folder
%     - subj - string, subject ID, e.g., 'P1010213'
%     - date - string, YYYYMMDD, e.g., 20190101
%     - ROI - string, e.g., OCC
%     - t1_folder - string, folder name
%     - metab_folder - string, folder name
%
% output = structure with fields:
%     - options - structure, above
%     - T1_out_file - string, file path
%     - MRS_mask_out - string, file path
%     - align_out_file - string, file path
%     - tissue_out_file - string, file path
%     - tissue_fract - vector, ** THIS IS THE FIELD OF INTEREST **
%
% N.B. paths have been removed, labed by ****, must be replaced to match local directories
%
% author: mps

%% opts
if ~exist('options','var')
    options = [];
end

if ~isfield(options,'top_dir')
    options.top_dir = '**** PATH TO TOP DIR GOES HERE ****';
end

if ~isfield(options,'scripts_path')
    options.scripts_path = '**** PATH TO SCRIPTS DIR GOES HERE ****';
end
addpath(genpath(options.scripts_path));

if ~isfield(options,'subj')
    options.subj = input('Subject ID (e.g., P1010213): ','s');
end
if ~isfield(options,'date')
    options.date = input('Scan date (e.g., 20171022): ','s');
end
if ~isfield(options,'ROI')
    options.ROI = input('ROI (e.g., OCC): ','s');
end
if ~isfield(options,'t1_folder')
    options.t1_folder = input('t1 folder name (e.g., MR-SE005-t1inplane_64sl_occ_2k): ','s');
end
if ~isfield(options,'metab_folder')
    options.metab_folder = input('metab folder name (e.g., MR-SE014-OCC_steam_eja_metab_RES): ','s');
end
if ~isfield(options,'overwrite')
    options.overwrite = 0; % assume no...
end
if ~isfield(options,'crop_MRS_T1')
    options.crop_MRS_T1 = 0; % assume no...
end

output = [];

%% list steps in order
% steps to run:
% 0) get a list of subjects, dates, and file names... happens outside and
% passed to this function one by one.

% 1) convert_MRS_T1.csh 
% 2) mps_make_MRS_mask.m
% 3) align_MRS_3T_T1.csh
% 4) make_MRS_tissue_masks.csh
% 5) pull in tissue fraction using 3dmaskave (AFNI):
% e.g., 3dmaskave -mask OCC_mask_al.nii.gz OCC_WM_mask.nii.gz

%% step 1: convert_MRS_T1.csh
% quick - takes about 2 s per subj

script_name = fullfile(options.scripts_path,'convert_MRS_T1.csh');

subj_dir = fullfile(options.top_dir,[options.subj '_' options.date]);

mkdir(subj_dir);

T1_out_file = fullfile(subj_dir, ['out.' options.ROI '.convert_MRS_T1.txt']);
if ~exist(T1_out_file,'file') || options.overwrite
    eval(['! rm -f ' T1_out_file]);

    cmd = ['! tcsh ' script_name ' ' options.subj ' ' options.date ' ' options.ROI ...
        ' ' options.t1_folder...
        ' |& tee ' T1_out_file];
    eval(cmd);

    output.T1_out_file = T1_out_file;
end

%% step 2: mps_make_MRS_mask.m
% quick - takes about 3 s per subj

mask_out_file = fullfile(subj_dir, [options.ROI '_mask.nii.gz']);

if ~exist(mask_out_file,'file') || options.overwrite
    eval(['! rm -f ' mask_out_file]);

    mask_opts = [];
    mask_opts.subj = options.subj;
    mask_opts.date = options.date;
    mask_opts.ROI = options.ROI;
    mask_opts.dicom_folder = options.metab_folder;

    output.MRS_mask_out = mps_make_MRS_mask(mask_opts);
end

%% step 3: align_MRS_3T_T1.sh
% slow-ish - takes about 2 min per subj

script_name = fullfile(options.scripts_path,'align_MRS_3T_T1.csh');

align_out_file = fullfile(subj_dir, ['out.' options.ROI '.align_MRS_3T_T1.txt']);

if ~exist(align_out_file,'file') || options.overwrite
    eval(['! rm -f ' align_out_file]);
    
    cmd = ['! tcsh ' script_name ' ' options.subj ' ' options.date ' ' options.ROI ...
        ' ' num2str(options.crop_MRS_T1) ' |& tee ' align_out_file];
    eval(cmd);
    
    output.align_out_file = align_out_file;
end

%% step 4: make_MRS_tissue_masks.sh
% quick - takes about 10 s per subj

script_name = fullfile(options.scripts_path,'make_MRS_tissue_masks.csh');

tissue_out_file = fullfile(subj_dir, ['out.' options.ROI '.make_MRS_tissue_masks.txt']);

if ~exist(tissue_out_file,'file') || options.overwrite
    eval(['! rm -f ' tissue_out_file]);

    cmd = ['! tcsh ' script_name ' ' options.subj ' ' options.date ' ' options.ROI...
        ' |& tee ' tissue_out_file];
    eval(cmd);

    output.tissue_out_file = tissue_out_file;
end

%% step 5: pull in tissue fraction using 3dmaskave:
% e.g., 3dmaskave -mask OCC_mask_al.nii.gz OCC_WM_mask.nii.gz
% quick - takes about 2 s per subj

tissue_labels = {'GM','WM','CSF'};

mask_file_name = fullfile(subj_dir, [options.ROI '_mask_al.nii.gz']);
    
for iT = 1:numel(tissue_labels)
    fract_out_file = fullfile(subj_dir, [options.ROI '_' tissue_labels{iT} '.1D']);
    
    if ~exist(fract_out_file,'file') || options.overwrite
        eval(['! rm -f ' fract_out_file]);

        tissue_file_name = fullfile(subj_dir, [options.ROI '_' tissue_labels{iT} ...
            '_mask.nii.gz']);

        cmd = ['! 3dmaskave -overwrite -quiet -mask ' mask_file_name ' ' ...
            tissue_file_name ' > ' fract_out_file];
        eval(cmd);
    end
    
    output.tissue_fract(iT) = dlmread(fract_out_file);
end


%% out
output.options = options;

end