function output = mps_run_all_MRS_tissue_correct(options)
% usage: output = mps_run_all_MRS_tissue_correct(options)
%
% options = structure with fields:
%     - top_dir = string, directory path for MRS data
%     - dicom_dir = string, diectory path for MRS dicom folders
%     - scripts_dir = string, directory path for MRS anatomy scripts
%     - overwrite
%    
% output = structure with fields:
%     - options = structure, as above
%     - tissue_fract = vector, GM WM CSF (out of 1), ** THIS IS THE
%     VARIABLE OF INTEREST **
%     - subj_date = matrix, n subjects x 2 (subj ID # & datenum)
%     - date_run = datestr, e.g. 'yyyy.mm.dd, HH:MM'
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

if ~isfield(options,'dicom_dir')
    options.dicom_dir = fullfile(options.top_dir,'dicom_data'); % defaults to this if not specified
end

if ~isfield(options,'scripts_dir')
    options.scripts_dir = '**** PATH TO SCRIPTS DIR GOES HERE ****';
end
addpath(genpath(options.scripts_dir));

if ~isfield(options,'overwrite')
    options.overwrite = 0; % assume no
end
if options.overwrite
    check_sure = questdlg(...
        'You have chosen to wipe all tissue correction files and start over (takes a long time), are you sure?',...
        'Sure?','Yes','No','No');
    if strcmp(check_sure,'No')
        warning('In that case, let''s just quit for now...');
        return
    end
end
if ~isfield(options,'fix_all_low_GM')
    options.fix_all_low_GM = 0; % assume no
end

output = [];

%% make a list of subject files
get_dicom_folders = dir(fullfile(options.dicom_dir,'P*'));

toss_me = [];
subj = [];
date_list = [];
subj_date_nums = [];
count_sessions = 0;
t1_folder_names = [];
metab_folder_names = [];

for iF = 1:numel(get_dicom_folders)
    check_name = regexp(get_dicom_folders(iF).name,'P\d\d\d\d\d\d\d_\d\d\d\d\d\d\d\d');
    
    if check_name == 1 && get_dicom_folders(iF).isdir
        count_sessions = count_sessions + 1;
        
        find_OCC_metab = dir(fullfile(options.dicom_dir,get_dicom_folders(iF).name,...
            'MR-SE*-OCC_steam_eja_metab_RES'));
        if ~isempty(find_OCC_metab)
            toss_file = []; % toss any that are not a folder
            for iFile = 1:numel(find_OCC_metab)
                if ~find_OCC_metab(iFile).isdir
                    toss_file = [toss_file ; iFile];
                end
            end
            find_OCC_metab(toss_file) = [];
            
            OCC_idx = numel(find_OCC_metab); % in case there is more than 1 metab scan, use the last one...
            metab_folder_names{count_sessions,1} = find_OCC_metab(OCC_idx).name;
        else
            metab_folder_names{count_sessions,1} = [];
        end
        
        find_OCC_t1 = dir(fullfile(options.dicom_dir,get_dicom_folders(iF).name,...
            'MR-SE*-OCC_t1inplane*'));
        if isempty(find_OCC_t1) % some OCC T1s have an old file name... check this?
            find_OCC_take2 = dir(fullfile(options.dicom_dir,get_dicom_folders(iF).name,...
                'MR-SE*t1*')); % any t1 folder...
            if ~isempty(find_OCC_take2)
                toss_file = []; % toss any that are not a folder
                for iFile = 1:numel(find_OCC_take2)
                    if ~find_OCC_take2(iFile).isdir | strfind(...
                            find_OCC_take2(iFile).name,'PFC') % can't be named PFC...
                        toss_file = [toss_file ; iFile];
                    end
                end
                find_OCC_take2(toss_file) = [];
            end
            if ~isempty(find_OCC_take2)
                OCC_t1_idx = numel(find_OCC_take2);
                find_OCC_t1 = find_OCC_take2(OCC_t1_idx);
            end
        end
        
        if ~isempty(find_OCC_t1)
            toss_file = []; % toss any that are not a folder
            for iFile = 1:numel(find_OCC_t1)
                if ~find_OCC_t1(iFile).isdir
                    toss_file = [toss_file ; iFile];
                end
            end
            find_OCC_t1(toss_file) = [];
            
            OCC_t1_idx = numel(find_OCC_t1); % in case there is more than 1 metab scan, use the last one...
            t1_folder_names{count_sessions,1} = find_OCC_t1(OCC_t1_idx).name; % 1 in second dim because OCC
        else
            t1_folder_names{count_sessions,1} = [];
        end
        
        find_PFC_metab = dir(fullfile(options.dicom_dir,get_dicom_folders(iF).name,...
            'MR-SE*-PFC_steam_eja_metab_RES'));
        if ~isempty(find_PFC_metab)
            toss_file = []; % toss any that are not a folder
            for iFile = 1:numel(find_PFC_metab)
                if ~find_PFC_metab(iFile).isdir
                    toss_file = [toss_file ; iFile];
                end
            end
            find_PFC_metab(toss_file) = [];
            
            PFC_idx = numel(find_PFC_metab); % in case there is more than 1 metab scan, use the last one...
            metab_folder_names{count_sessions,2} = find_PFC_metab(PFC_idx).name; % 2 in 2nd dim because PFC
        else
            metab_folder_names{count_sessions,2} = [];
        end
        
        find_PFC_t1 = dir(fullfile(options.dicom_dir,get_dicom_folders(iF).name,...
            'MR-SE*-PFC_t1inplane*')); % don't look for old file naming system for PFC...
        if ~isempty(find_PFC_t1)
            toss_file = []; % toss any that are not a folder
            for iFile = 1:numel(find_PFC_t1)
                if ~find_PFC_t1(iFile).isdir
                    toss_file = [toss_file ; iFile];
                end
            end
            find_PFC_t1(toss_file) = [];
            
            PFC_t1_idx = numel(find_PFC_t1); % in case there is more than 1 metab scan, use the last one...
            t1_folder_names{count_sessions,2} = find_PFC_t1(PFC_t1_idx).name; % 2 in second dim because PFC
        else
            t1_folder_names{count_sessions,2} = [];
        end
        
        if ~isempty(metab_folder_names{count_sessions,1}) || ...
                ~isempty(metab_folder_names{count_sessions,2})
            % if there is metab data
            subj{count_sessions} = get_dicom_folders(iF).name(1:8);
            date_list{count_sessions} = get_dicom_folders(iF).name(10:17);
        
            subj_date_nums = [subj_date_nums ; str2num(...
                subj{count_sessions}(2:end)) datenum(date_list{count_sessions},...
                'yyyymmdd')];
        else % if no metab data...
            toss_me = [toss_me ; iF];
            metab_folder_names(count_sessions,:) = []; % remove this row
            count_sessions = count_sessions - 1; % un-count this person
        end
        
    else 
        toss_me = [toss_me ; iF];
    end
end
get_dicom_folders(toss_me) = [];

missing_t1_idx = [];
for iSubj = 1:numel(subj)
    for iROI = 1:size(t1_folder_names,2)
        if isempty(t1_folder_names{iSubj,iROI}) && ~isempty(metab_folder_names{iSubj,iROI})
            missing_t1_idx = [missing_t1_idx ; iSubj iROI]; % 1 = OCC missing, 2 = PFC
        end
    end
end
if ~isempty(missing_t1_idx)
    error(['Can''t find T1 for: ' missing_t1_idx]);
end

%% run the tissue correction for each subject
tissue_opts = [];
tissue_opts.top_dir = fullfile(options.top_dir,'anatomy');
tissue_opts.scripts_path = options.scripts_dir;

ROI_names = {'OCC','PFC'};
tissue_fract = nan(numel(subj),size(t1_folder_names,2),3);

h_wait = waitbar(0,'Loading tissue fraction data, please wait...');

for iSubj = 1:numel(subj)
    for iROI = 1:size(t1_folder_names,2)
        if ~isempty(metab_folder_names{iSubj,iROI})
            
            tissue_opts.subj = subj{iSubj};
            tissue_opts.date = date_list{iSubj};
            tissue_opts.ROI = ROI_names{iROI};
            tissue_opts.t1_folder = t1_folder_names{iSubj,iROI};
            tissue_opts.metab_folder = metab_folder_names{iSubj,iROI};
            
            tissue_opts.overwrite = options.overwrite; % hope you're sure...
            
            tissue_out{iSubj,iROI} = mps_MRS_tissue_correction(tissue_opts);
            
            tissue_fract(iSubj,iROI,1:3) = tissue_out{iSubj,iROI}.tissue_fract;
            
        end
    end
    waitbar(iSubj/numel(subj), h_wait);
end

close(h_wait);

%% identify possibly miss-aligned datasets
% figure; hist(tissue_fract(:,:,1))

low_GM_thresh = 0.35; % based on visual inspection of histogram above

low_GM_OCC_idx = find(tissue_fract(:,1,1) < low_GM_thresh); 
low_GM_PFC_idx = find(tissue_fract(:,2,1) < low_GM_thresh);

both_idx{1} = low_GM_OCC_idx;
both_idx{2} = low_GM_PFC_idx;

if options.fix_all_low_GM
    for iROI = 1:size(t1_folder_names,2)
        
        for iSubj = 1:numel(both_idx{iROI})
            if ~isempty(metab_folder_names{iSubj,iROI})
                
                tissue_opts.subj = subj{both_idx{iROI}(iSubj)};
                tissue_opts.date = date_list{both_idx{iROI}(iSubj)};
                tissue_opts.ROI = ROI_names{iROI};
                tissue_opts.t1_folder = t1_folder_names{...
                    both_idx{iROI}(iSubj),iROI};
                tissue_opts.metab_folder = metab_folder_names{...
                    both_idx{iROI}(iSubj),iROI};
                
                tissue_opts.overwrite = 1; % need to overwrite for these subjects to fix low GM...
                tissue_opts.crop_MRS_T1 = 1; % crop the MRS T1 to try to fix alignment to 3T T1
                
                tissue_out{both_idx{iROI}(iSubj),iROI} = ...
                    mps_MRS_tissue_correction(tissue_opts);
                
                tissue_fract(both_idx{iROI}(iSubj),iROI,1:3) = ...
                    tissue_out{both_idx{iROI}(iSubj),iROI}.tissue_fract;
                
            end
        end
    end
    
end

%% run MNI transformation
script_name = fullfile(options.scripts_dir,'transform_MRS_voxel_SUMA_to_MNI_script.csh');

h_wait = waitbar(0,'Converting MRS voxels to MNI space, please wait...');

for iSubj = 1:numel(subj)
    for iROI = 1:size(t1_folder_names,2)
        mni_folder = fullfile(options.top_dir,'anatomy',[subj{iSubj} '_' ...
            date_list{iSubj}],'MNI');
        mni_file = fullfile(mni_folder,[ROI_names{iROI} '_mask_mni.nii.gz']);
        exclude_file = fullfile(mni_folder,'exclude',[ROI_names{iROI} '_mask_mni.nii.gz']);
        if ~isempty(t1_folder_names{iSubj,iROI}) && ~exist(exclude_file,'file') && ...
                ( ~exist(mni_folder,'dir') || ~exist(mni_file,'file') || ...
                options.overwrite )
            
            mkdir(mni_folder)
            
            mni_out_file = fullfile(mni_folder, ['out.' ROI_names{iROI}...
                '.MNI.txt']);
            
            if iROI == 1
                eval(['! rm -f ' mni_out_file]);
            end
            
            mni_opts.subj = subj{iSubj};
            mni_opts.date = date_list{iSubj};
            mni_opts.ROI = ROI_names{iROI};
            
            cmd = ['! tcsh ' script_name ' ' mni_opts.subj ' ' mni_opts.date ...
                ' ' mni_opts.ROI ' |& tee ' mni_out_file];
            eval(cmd);
            
            output.mni_out_file{iSubj,iROI} = mni_out_file;
            
        end
    end
    waitbar(iSubj/numel(subj), h_wait);
end
close(h_wait)

%% output
output.tissue_fract = tissue_fract;
output.subj_date = subj_date_nums;
output.tissue_out = tissue_out;
output.options = options;
output.date_run = datestr(now,'yyyy.mm.dd, HH:MM');
end