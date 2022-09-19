function output = mps_make_MRS_mask(options)
% usage: output = mps_make_MRS_mask(options)
%
% options = structure with fields:
%     - subj (str, format: 'P#######')
%     - date (str, format: 'YYYYMMDD')
%     - ROI (str, valid options = 'OCC', 'PFC')
%     - dicom_folder (str)
%     - dicom_file (str)
%
% output = structure with fields:
%   - options
%
% N.B. paths have been removed, labed by ****, must be replaced to match local directories
%
% author: mps

%% opts
if ~exist('options','var')
    options = [];
end
if ~isfield(options,'subj')
    options.subj = input('Subject ID (e.g., P1010213): ','s');
end
subj = options.subj;

if ~isfield(options,'date')
    options.date = input('Scan date (e.g., 20171022): ','s');
end
subj_date = [subj '_' options.date];

if ~isfield(options,'ROI')
    options.ROI = questdlg('Which ROI?','ROI','OCC','PFC','OCC');
end

if strcmp(lower(options.ROI),'occ')
    t1_name = 't1_OCC';
    voxel_name = 'OCC';
elseif strcmp(lower(options.ROI),'pfc')
    t1_name = 't1_PFC';
    voxel_name = 'PFC';
end

if ~isfield(options,'dicom_folder')
    options.dicom_folder = input('Metab dicom folder name (e.g., MR-SE013-OCC_steam_eja_metab): ','s');
end
dicom_folder = options.dicom_folder;

% n.b. options.dicome_file is handled below, due to path def issues!

%%

addpath(genpath('**** PATH TO GANNET DIR GOES HERE ****/Gannet3.0-master'))
addpath(genpath('**** PATH TO CODE DIR GOES HERE ****'))

% assuming you have run:
% 1) convert_MRS_T1.csh 

top_dir = '**** PATH TO TOP DIR GOES HERE ****';

subj_dir = fullfile(top_dir,'anatomy',subj_date);

gz_t1 = fullfile(subj_dir,[t1_name '.nii.gz']);
nii_t1 = fullfile(subj_dir,[t1_name '_niiformat_.nii']);

eval(['! 3dcopy -overwrite ' gz_t1 ' ' nii_t1]);

MRS_dicom = fullfile(top_dir,'dicom_data',subj_date,dicom_folder);

if ~isfield(options,'dicom_file')
    warning(['Assuming the first .dcm file in this folder is fine: ' MRS_dicom]);
    get_dcm = dir(fullfile(MRS_dicom, '*.dcm'));
    dicom_file = get_dcm(1).name;
else
    dicom_file = options.dicom_file; % use one if provided
end

MRS_filename = fullfile(MRS_dicom,dicom_file);

dicom_copy_dir = fullfile(subj_dir,[options.ROI '_voxel_dicom_copy']);
mkdir(dicom_copy_dir)
copyfile(MRS_filename,dicom_copy_dir)

MRS_copy_filename = fullfile(dicom_copy_dir,dicom_file);

options.target_dir = dicom_copy_dir;

[Pos] = extract_MRS_voxel_pos(options);

clear MRS_struct

dcmHeader = Pos.mrprot; % pull this using Romain's matspec code

% pull these using DICOMRead.m and read_dcm_header.m from Gannet
ii = 1;

missing_fields = 0;
if isfield(dcmHeader.sSpecPara.sVoI,'dInPlaneRot')
DicomHeader.VoI_InPlaneRot       = dcmHeader.sSpecPara.sVoI.dInPlaneRot; % Voxel rotation in plane
missing_fields = 1;
else 
DicomHeader.VoI_InPlaneRot       = 0;
missing_fields = 1;
end
DicomHeader.VoI_RoFOV            = dcmHeader.sSpecPara.sVoI.dReadoutFOV; % Voxel size in readout direction [mm]
DicomHeader.VoI_PeFOV            = dcmHeader.sSpecPara.sVoI.dPhaseFOV; % Voxel size in phase encoding direction [mm]
DicomHeader.VoIThickness         = dcmHeader.sSpecPara.sVoI.dThickness; % Voxel size in slice selection direction [mm]
if isfield(dcmHeader.sSpecPara.sVoI.sNormal,'dCor')
DicomHeader.NormCor              = dcmHeader.sSpecPara.sVoI.sNormal.dCor; % Coronal component of normal vector of voxel
else
DicomHeader.NormCor              = 0;
missing_fields = 1;
end
if isfield(dcmHeader.sSpecPara.sVoI.sNormal,'dSag')
DicomHeader.NormSag              = dcmHeader.sSpecPara.sVoI.sNormal.dSag; % Sagittal component of normal vector of voxel
else
DicomHeader.NormSag              = 0;
missing_fields = 1;
end
if isfield(dcmHeader.sSpecPara.sVoI.sNormal,'dTra')
DicomHeader.NormTra              = dcmHeader.sSpecPara.sVoI.sNormal.dTra; % Transversal component of normal vector of voxel
else
DicomHeader.NormTra              = 0;   
missing_fields = 1;
end
DicomHeader.PosCor               = dcmHeader.sSpecPara.sVoI.sPosition.dCor; % Coronal coordinate of voxel [mm]
DicomHeader.PosSag               = dcmHeader.sSpecPara.sVoI.sPosition.dSag; % Sagittal coordinate of voxel [mm]
DicomHeader.PosTra               = dcmHeader.sSpecPara.sVoI.sPosition.dTra; % Transversal coordinate of voxel [mm]
MRS_struct.p.voxdim(ii,1) = DicomHeader.VoI_PeFOV;
MRS_struct.p.voxdim(ii,2) = DicomHeader.VoI_RoFOV;
MRS_struct.p.voxdim(ii,3) = DicomHeader.VoIThickness;
MRS_struct.p.VoI_InPlaneRot(ii) = DicomHeader.VoI_InPlaneRot;
MRS_struct.p.voxoff(ii,1) = DicomHeader.PosSag;
MRS_struct.p.voxoff(ii,2) = DicomHeader.PosCor;
MRS_struct.p.voxoff(ii,3) = DicomHeader.PosTra;
MRS_struct.p.NormCor(ii) = DicomHeader.NormCor;
MRS_struct.p.NormSag(ii) = DicomHeader.NormSag;
MRS_struct.p.NormTra(ii) = DicomHeader.NormTra;

% need to give this some weird indexing input params...
vox = {voxel_name}; % give the voxel a name
kk = 1; % indexing

% use Gannet to make the voxel mask
MRS_struct = GannetMask_SiemensTWIX(MRS_copy_filename, nii_t1, MRS_struct, ...
    ii, vox, kk);

file_name = [voxel_name '_mask'];
file_ext = '.nii.gz';
put_file_in_path = fullfile(subj_dir,[file_name file_ext]);

eval(['! 3dcopy ' MRS_struct.mask.(vox{kk}).outfile{1} ' ' put_file_in_path]);
% fix afni tlrc issue
eval(['! 3drefit -view orig -space ORIG ' put_file_in_path]);
eval(['! rm ' nii_t1]);
%% out
output.options = options;
output.MRS_struct = MRS_struct;
output.file_path = put_file_in_path;
output.missing_fields = missing_fields;
%%
end