function [Pos] = extract_MRS_voxel_pos(options)
% usage: [Pos] = extract_MRS_voxel_pos(options)
%
% dependencies: explore_spectro_data.m and parse_siemens_shadow.m (which
% have their own...)
%
% N.B. paths have been removed, labed by ****, must be replaced to match local directories
%
% mps 2018.11.20

%% opt
if ~exist('options','var')
    options = [];
end
if ~isfield(options,'target_dir')
    error('No target directory provided!')
end
%%

%%% add romain's code from matspec
addpath(genpath('**** PATH TO MATSPEC TOOLBOX GOES HERE ****'))

[afid, dicom_struct]=spec_read_all(options.target_dir);

[imghdr,serhdr,mrprot]=parse_siemens_shadow(dicom_struct(1));

Pos.VoiFOV = [ imghdr.VoiReadoutFoV imghdr.VoiPhaseFoV imghdr.VoiThickness];
Pos.VoiOrientation = reshape(imghdr.ImageOrientationPatient,[3,2]);
Pos.VoiOrientation(:,3) = imghdr.VoiOrientation;
Pos.VoiPosition = imghdr.VoiPosition;
Pos.VoiInPlaneRotation = imghdr.VoiInPlaneRotation;
Pos.mrprot = mrprot;

end