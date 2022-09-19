function output = single_page_phcp_func(options)
% useage: output = single_page_phcp_func(options)
%
% N.B. paths have been removed, labed by ****, must be replaced to match local directories
%
% mps 20190205

%% set options
if ~exist('options','var')      
    options = [];
end
if ~isfield(options,'displayFigs')
    options.displayFigs = 1; % 1 = yes, 0 = no
end

% choose between OCC & PFC...
if ~isfield(options,'which_ROI')
    options.which_ROI = questdlg('Which ROI do you want to analyze?','Which ROI?','OCC','PFC','OCC');
end
if strcmp(options.which_ROI,'OCC')
    ROI_idx = 1;
elseif strcmp(options.which_ROI,'PFC')
    ROI_idx = 2;
end

% close figures after saving them? 1 = yes, 0 = no
if ~isfield(options,'close_all')
    options.close_all = 1;
end

% set frequency & phase correction options
if ~isfield(options,'freq_phase_corr')
    options.freq_phase_corr = '(max + abs) x2 + real';
    % valid options are:
    %   (max + abs) x2 + real
    %   corr
    %   corr w/ bounds
end

% set option for which part of the process you want to run
if ~isfield(options,'which_step')
    options.which_step = questdlg('Which processing step do you want to perform?',...
        'Which step?','pre-LCM','LCM','post-LCM','pre-LCM');
end
if ~sum(strcmp(lower(options.which_step), ...
        lower({'pre-LCM','LCM','post-LCM'}) ))
    error(['Unrecognized value for options.which_step: ' options.which_step]);
end

% set option for how to exclude bad data -- manually vs. automatic


if ~isfield(options,'which_control_file')
    options.which_control_file = 'steam_phcp_lipids';
    % set the input option string for processing_LCmodel.m -- choose which
    % control file settings to use
end

if ~isfield(options,'output_suffix')
    options.output_suffix = '';
    % set a string for the output files in the post-LCM step, blank by
    % default
end

output = [];

%% get the paths
    
%%% add romain's code from matspec
addpath(genpath('**** PATH TO MATSPEC DIR GOES HERE ****/matspec/'))

%%% add our own custom functions at the beginning
addpath(genpath('**** PATH TO MATLAB CODE GOES HERE ****'),'-begin')

%%% add spm8 to the END of the paths
addpath(genpath('**** PATH TO SPM8 GOES HERE ****/spm8'),'-end')
    

%% set processing parameters
if ~isfield(options,'par')
    par = processing_spec;
    par.mean_line_broadening=4;

    % params for relaxation, water correction, from Gosia 20190610
    par.gmT1 = 2130; % mps 20220628 changed from 2132 -- matches marjanska 2017
    par.gmT2 = 50; 
    par.wmT1 = 1220;
    par.wmT2 = 55;
    par.csfT1 = 4425;
    par.csfT2 = 141;
    par.TR = 5000;
    par.TE = 8;
    par.water_fraction = [0.80 0.71 0.97];
    
end

if ~isfield(par,'figure')
    % show figures at all? 1 = yes, 0 = no
    if options.displayFigs
        par.figure = 1;
    else
        par.figure = 0;
    end
end

%% now split into 3 processing steps

if strcmp(lower(options.which_step), 'pre-lcm')
%% check matlab version
if datenum(version('-date')) > datenum('February 11, 2014')
    error(['This code relies on SPM8, and will NOT function with versions '...
        'of Matlab beyond 2014a!!'])
end

%% for subjects with an issue with w1, use a different water reference
subj_with_w1_issues = {'P6004071_20180801/MR-SE028-OCC_steam_eja_w1/'};

alternative_h2o_ref = {'P6004071_20180801/MR-SE030-OCC_steam_eja_w4_RES/'};

%% Throw out known bad data points for particular scans

% OCC first, ROI_idx = 1
subj_with_data_to_toss{1} = {'P6010622_20180908','P2110417_20181029',...
    'P1010213_20180211','P6004213_20190116','P6004663_20180911',...
    'P6010465_20180825','P1010309_20191221','P3211899_20201024',...
    'P2112274_20210504','P6012167_20210622','P6012232_20210807',...
    'P6010932_20211008','P6011566_20200127','P6011098_20190507',...
    'P6010956_20190521','P6010731_20181114','P6010692_20210828',...
    'P6010622_20190119','P6010616_20181020','P6010465_20181117',...
    'P3102476_20190513','P2104777_20180730','P1010309_20171130',...
    'P1010063_20171105','P6012127_20220311','P6010983_20220406',...
    'P6011566_20220418','P6012284_20220628'};

TRs_to_toss{1} = {[2,4,8,23,29,32,36,49,56,62,79],[78],...
    [59],[24],[86],[1,22,31,49,58,59,79,80],...
    [34 35],[41,62,9,70,56,87,27,82,85,92,84,30,71,7,13,86,77]...
    [45,95],[34,42,57,58,60,81],[78],[3,7,25,54,65,67,76,82,92],...
    [8,13,94],[38,42],[82],[26,37,89],[16,26],[88,90,92],[1,5,37],...
    [9,26,27,42,79],[40,70],[40,48,58,60,62],[38,43,69],[7,8,77,80,95],...
    [67,48,33,58,41,80,1],[64,50,24,70,9,85,31,94,37],[71,31],[34]};

% PFC 2nd, ROI_idx = 2
subj_with_data_to_toss{2} = {'P6011098_20190507','P2111457_20210330',...
    'P6012167_20210622','P5102243_20211001','P1011169_20191205',...
    'P1006162_20191207','P3111282_20200111','P6011071_20200121',...
    'P6011566_20200127','P6011275_20211124','P6011227_20200304',...
    'P6010465_20181117','P6010465_20180825','P6010445_20181102',...
    'P6010322_20180820','P6004737_20180912','P6004687_20180616',...
    'P6004663_20180911','P6004604_20180108','P6004231_20181229',...
    'P6004213_20190319','P5110387_20200925','P4104647_20190330',...
    'P3104042_20180106','P1010228_20180225','P6012284_20220214',...
    'P6012127_20220311','P6004172_20220413','P6011747_20220708'};

TRs_to_toss{2} = {[42],[51],[35,19,78,89,37,36,12,70,60,95,18],...
    [31,4],[32],[44,18,54,25,64,63,82],[65,32],[53],[60,92,2],...
    [92,80],[83],[35],[1,15,16,17,48,67,83,84,96],[9,90],[72,39],...
    [14],[112],[69,76],[35,36,37,38],[87],[27],[3,7],[59],...
    [9,20,43,60,78],[38],[60,54,46,80],[11,12,9,21,60],[76],[23]};

%% find metab spectra
d=get_subdir_regex('**** PATH TO DICOM DATA GOES HERE****/dicom_data','P\d\d\d\d\d\d\d*',...
    ['MR-SE\d\d\d-' options.which_ROI '_steam_eja_metab']);
toss_me = [];
for iD = 1:numel(d)
    if isempty(strfind(d{iD},'RES'))
        toss_me = [toss_me iD];
    end
end
d(toss_me) = [];

%% find water spectra
dw=get_subdir_regex('**** PATH TO DICOM DATA GOES HERE****/dicom_data','P\d\d\d\d\d\d\d*',...
    ['MR-SE\d\d\d-' options.which_ROI '_steam_eja_w1']);
toss_me = [];
issue_list = [];
for iD = 1:numel(dw)
    if ~isempty(strfind(dw{iD},'noOVS'))
        toss_me = [toss_me iD];
    end
    find_issue_idx = []; % clear this
    for iIssue = 1:numel(subj_with_w1_issues)
        find_issue_idx = strfind(dw{iD},subj_with_w1_issues{iIssue});
        if ~isempty(find_issue_idx)
            dw{iD} = fullfile(dw{iD}(1:find_issue_idx-1),...
                alternative_h2o_ref{iIssue});
        end
    end
    if ~isempty(find_issue_idx)
        issue_list(iD) = 1;
    else issue_list(iD) = 0;
    end
end
dw(toss_me) = [];
issue_list(toss_me) = [];
issue_idx = find(issue_list);

%% reading in the data and organizing 
% metab data
f=explore_spectro_data(char(d));

warndlg('Crudely tossing any scan that has the same name and date as scan after it, assuming this is an unusable data set that was repeated and should be tossed...');
toss_me = [];
for iF = 1:(numel(f)-1) % can't include last one...
    if strcmp(f(iF).sujet_name , f(iF+1).sujet_name)
        warning(['tossing suspected duplicate metab scan for ' f(iF).sujet_name])
        toss_me = [toss_me iF];
    end
end
f(toss_me) = [];

f=concatenate_fid(f);

% water data
fw=explore_spectro_data(char(dw));

toss_me = [];
for iF = 1:(numel(fw)-1) % can't include last one...
    if strcmp(fw(iF).sujet_name , fw(iF+1).sujet_name)
        warning(['tossing suspected duplicate w1 scan for ' fw(iF).sujet_name])
        toss_me = [toss_me iF];
    end
    if sum(issue_idx == iF)
        fw(iF).fid = fw(iF).fid(:,1);
        % only use the first of the w4 series
    end
end
fw(toss_me) = [];

% check that subjects in f & fw match...

output.subj_date = [];
doesnt_match = [];
for iSubj = 1:min([numel(f) numel(fw)])
    if ~strcmp(f(iSubj).sujet_name, fw(iSubj).sujet_name)
        doesnt_match = [doesnt_match ; iSubj];
    end
    
    output.subj_date{iSubj,1} = f(iSubj).sujet_name;
end
if ~isempty(doesnt_match)
    error(['Some scan names don''t match, start by looking at ' ...
        f(doesnt_match(1)).sujet_name]);
end

if numel(f) ~= numel(fw)
    error(['Number of subjects in f (metab data) = ' num2str(numel(f)) ...
        ' doesn''t equal number in fw (water reference) = ' num2str(numel(fw)) ...
        ' ... check for an incomplete scan??']);
end

% initial processing
% eddy current compensation
f_ecc = eddycorrection(f, fw);
fw_ecc = eddycorrection(fw, fw);

% remove first point and add extra 0 at the end (to have the same number of
% points as initially
fo = remove_first_points_fillup(f_ecc, 1);

%% toss known bad TRs
% mps 20190111 - adding the ability to toss TRs...
% to check for bad TRs: mps_check_bad_avgs(fo, subj_idx, par)
% where subj_idx is the # representing where in the list of subjects this person is (the Nth subject)
% use the data cursor to select the bad data in the plot, the z value is
% the TR # to exclude. par is optional, include if you want to run line
% broadening! Can also be used for other (e.g., processed) data sets, such
% as fc, rather than fo. For example: mps_check_bad_avgs(fc, 83, par)

n_toss = 0;
for iSubj = 1:numel(fo)
    find_toss_idx = find(strcmp(fo(iSubj).sujet_name,subj_with_data_to_toss{ROI_idx})); % find the subject in the toss list
    if ~isempty(find_toss_idx)
        fo(iSubj).fid(:,TRs_to_toss{ROI_idx}{find_toss_idx}) = []; % find which TRs to toss for this person, and then toss them
        fo(iSubj).Nex = fo(iSubj).Nex - numel(TRs_to_toss{ROI_idx}{find_toss_idx}); 
        fo(iSubj).Number_of_spec = fo(iSubj).Number_of_spec - numel(TRs_to_toss{ROI_idx}{find_toss_idx});
        n_toss = n_toss +1;
        warning(['Tossing TRs ' num2str(TRs_to_toss{ROI_idx}{find_toss_idx}) ...
            ' for ' fo(iSubj).sujet_name ', as requested...']);
    end
end
if n_toss > 0
    warndlg('Crudely tossing some TRs, as specified!')
end

%% freq & phase correction 
corr_str = {'corr','correl','correlation','correlate'};
corr_bound_str = {'corr with bound','correlation with bound','corr with bounds',...
    'correlation with bounds','corr. with bound','corr. with bounds',...
    'corr w/ bound','corr w/ bounds','correlation w/ bound','correlation w/ bounds',...
    'corr_bound','correlation_bound'};
max_abs_real_str = {'(max + abs) x2 + real', 'max + abs, real','max abs real'};

if sum(strcmp(lower(options.freq_phase_corr) , corr_str))
%%% option #1 = Corr
    par.method='correlation';
    par.correlation_bound = [];
    fc = processing_spec(fo,par);

    % par.same_fig = 1; % turn this on to plot on the same figure;
    % par.arg_give_me_a_new_one = 1; % choose figure number
    for iSubj = 1:numel(fo)
    plot_spectrum(fo(iSubj),par) % before processing
    get_ax = axis;
    axis([0.5 2.5 get_ax(3) get_ax(4)]);
    title([fo(iSubj).sujet_name ' Before'])
    set(gcf,'color','w')
    end

    for iSubj = 1:numel(fo)
    plot_spectrum(fc(iSubj),par) % after processing
    get_ax = axis;
    axis([0.5 2.5 get_ax(3) get_ax(4)]);
    title([fc(iSubj).sujet_name ' 1) Corr.'])
    set(gcf,'color','w')
    end

% % to know if frequency and phase correction were successful, look for
% % variability in the peak freq of NAA (~2ppm - for freq) and variability in
% % the shape (e.g., weird dips) on the flanks of the NAA peak (~1.95ppm -
% % for phase).

elseif sum(strcmp(lower(options.freq_phase_corr) , corr_bound_str))
%%% option #2 = corr w/ bounds
    if ~isfield(par,'correlation_bound')
        par.correlation_bound = [1.8 3.5];
        warning(['Using default correlation bounds for freq. & phase correction: '...
            num2str(par.correlation_bound) ]);
    end
    par.method='correlation';
    fc = processing_spec(fo,par);

    for iSubj = 1:numel(fo)
        plot_spectrum(fc(iSubj),par) % after processing
        get_ax = axis;
        axis([0 6 get_ax(3) get_ax(4)]);
        title([fo(iSubj).sujet_name ' 2) Corr. w/ bound'])
        set(gcf,'color','w')
    end

elseif sum(strcmp(lower(options.freq_phase_corr) , max_abs_real_str))
%%% option #3 = (max + abs) x2 & real

    par.method='max';
    par.correct_freq_mod='abs';
    fc_1 = processing_spec(fo,par);
    if options.close_all
        close all
    end
    par.correct_freq_mod='abs';
    fc_2 = processing_spec(fc_1,par);
    if options.close_all
        close all
    end
    par.correct_freq_mod='real';
    fc = processing_spec(fc_2,par);
    if options.close_all
        close all
    end
    
else
    error(['Unknown value for options.freq_phase_corr: ' options.freq_phase_corr]);
end

%% show & save some figures for freq. & phase correction
plot_dir = fullfile('**** PATH TO SAVED PLOT DIR GOES HERE ****/saved_plots',options.which_ROI);
plot_dir_contents = dir([plot_dir '/*.fig']);
if ~isempty(plot_dir_contents)
    clear ask_wipe
    ask_wipe = ['Saved plots folder is not empty (' plot_dir ...
        '), do you want to delete all contents and re-write, or quit?'];
    wipe_dir = questdlg(ask_wipe,'Do you want to delete?','Delete','Quit','Quit');
    if strcmp(wipe_dir,'Delete')
        warning(['Deleting contents of ' plot_dir ', as requested...']);
        eval(['! rm -f ' plot_dir '/*.fig']);
    elseif strcmp(wipe_dir,'Quit')
        return
    end
end

if options.displayFigs & par.figure % if we are plotting figures...
    for iSubj = 1:numel(fo)
        plot_spectrum(fo(iSubj),par) % before processing
        get_ax = axis;
        axis([0 6 get_ax(3) get_ax(4)]);
        title([fo(iSubj).sujet_name ' uncorrected'])
        set(gcf,'color','w')
        savefig(fullfile(plot_dir,[fo(iSubj).sujet_name '_' options.which_ROI '_uncorrected.fig']))
        if options.close_all
            close(gcf);
        end
        
        plot_spectrum(fc(iSubj),par) % after processing
        get_ax = axis;
        axis([0 6 get_ax(3) get_ax(4)]);
        title([fo(iSubj).sujet_name ' 3) Max + Abs. x2 & Real'])
        set(gcf,'color','w')
        savefig(fullfile(plot_dir,[fo(iSubj).sujet_name '_' options.which_ROI '_corrected.fig']))
        if options.close_all
            close(gcf);
        end
        
        
        output.SD_NAA(iSubj) = mps_SD_NAA(fc(iSubj),par);
    end
end

%% to obtain water linewidth
fw_ecc = get_water_width(fw_ecc, par.figure);
output.water_width_no_cor = [];
for iS = 1:numel(fw_ecc)
    output.water_width_no_cor(iS,1) = fw_ecc(iS).water_width_no_cor;
end

if options.close_all
    close all
end

%% preparing for LCModel analysis:

pp.root_dir=['**** PATH TO PROCESSED DATA GOES HERE ****/processed_data/' options.which_ROI];
% it uses fc.sujet_name and fc.SerDescr for naming RAW files
pp.gessfile=5; % different options for setting file names based on dicom info

% remove exisiting proc files
proc_dir_contents = dir(fullfile(pp.root_dir,'*.RAW'));
if ~isempty(proc_dir_contents)
    ask_wipe = ['Processed data folder is not empty (' pp.root_dir '), do you want to delete all contents and re-write, or quit?'];
    wipe_dir = questdlg(ask_wipe,'Do you want to delete?','Delete','Quit','Quit');
    if strcmp(wipe_dir,'Delete')
        warning(['Deleting contents of ' pp.root_dir ', as requested...']);
        eval(['! rm ' pp.root_dir '/*.PLOTIN']);
        eval(['! rm ' pp.root_dir '/*.RAW']);
        eval(['! rm ' pp.root_dir '/*.H2O']);
    elseif strcmp(wipe_dir,'Quit')
        return
    end
end

write_fid_to_lcRAW(fc,pp,fw_ecc);

% remove existing lcm files
lcm_fit_dir = fullfile('**** PATH TO PROCESSED DATA GOES HERE ****/processed_data/', options.which_ROI,'lcm_fit');
lcm_fit_contents = dir(lcm_fit_dir);
if ~isempty(lcm_fit_contents)
    clear ask_wipe
    ask_wipe = ['LCM folder is not empty (' lcm_fit_dir '), do you want to delete all contents and re-write, or quit?'];
    wipe_dir = questdlg(ask_wipe,'Do you want to delete?','Delete','Quit','Quit');
    if strcmp(wipe_dir,'Delete')
        warning(['Deleting contents of ' lcm_fit_dir ', as requested...']);
        eval(['! rm -f ' lcm_fit_dir '/*.CONTROL']);
        eval(['! rm -f ' lcm_fit_dir '/*.COORD']);
        eval(['! rm -f ' lcm_fit_dir '/*.PRINT']);
        eval(['! rm -f ' lcm_fit_dir '/*.PS']);
    elseif strcmp(wipe_dir,'Quit')
        return
    end
end

output.fo = fo;
output.fc = fc;

%% run the LCModel analysis
elseif strcmp(lower(options.which_step), 'lcm')

    if datenum(version('-date')) > datenum('February 11, 2014')
        error(['This code relies on SPM8, and will NOT function with versions '...
            'of Matlab beyond 2014a. However, it SHOULD be run on Matlab 2009a for historical reasons.'])
    end

    processing_LCmodel(options.which_control_file,'lcm_fit')

%% post-LCModel processing
elseif strcmp(lower(options.which_step), 'post-lcm')

%% check matlab version & server
if datenum(version('-date')) > datenum('February 11, 2014')
    error(['This code relies on SPM8, and will NOT function with versions '...
        'of Matlab beyond 2014a!!'])
end


dir_res=get_subdir_regex;
concat_ps_file(dir_res)


%% convert the data files to .pdf and .csv
% 1. generate pdf file for review of the fits
% be sure to select the folder you wrote the LCmodel data to in the step
% above, e.g., lcm_fit

if ~exist('proc_dir','var')
    proc_dir = '**** PATH TO PROCESSED DATA GOES HERE ****/processed_data';
end

% check for afni
[foo, result] = system('which afni');
if ~isempty(strfind(result,'afni: Command not found.'))
    error('You need to add afni to your path, in case there are new MRS anatomy files to process.');
end

% 2. generate spreadsheet

% fix file permissions for the files you just wrote here...
eval(['! chmod g+w -R ' dir_res{1}]);

% check if we know which ROI to use
if numel(dir_res) > 1
    error('You selected more than 1 lcm folder...')
end
if ~exist('options.which_ROI','var')
    occ_idx = regexp(dir_res{1},'OCC');
    pfc_idx = regexp(dir_res{1},'PFC');
    if isempty(occ_idx) && isempty(pfc_idx)
        error('options.which_ROI is not defined, and was not detected automatically from the lcm folder name!')
    elseif ~isempty(occ_idx) && ~isempty(pfc_idx)
        error('options.which_ROI is not defined, and the lcm folder name has BOTH OCC & PFC in it??')
    elseif ~isempty(occ_idx) && isempty(pfc_idx)
        options.which_ROI = 'OCC';
        warning(['automatically detected which ROI (' options.which_ROI ') based on lcm folder name']);
    elseif isempty(occ_idx) && ~isempty(pfc_idx)
        options.which_ROI = 'PFC';
        warning(['automatically detected which ROI (' options.which_ROI ') based on lcm folder name']);
    end
end

c=get_result(dir_res);
write_name = fullfile(proc_dir,...
    [datestr(now,'yyyymmdd') '_phcp_' options.which_ROI '_' num2str(numel(c.suj)) ...
    'subj_unscaled' options.output_suffix '.csv']);
if ~exist(write_name,'file')
    write_conc_res_to_csv(c,write_name)
else
    error(['The following file already exists, to create a new version, you must delete the existing one! - ' write_name]);
end

% scale to tCr
c_cr = correct_result_ration(c,'','Cr_PCr',8);
write_name = fullfile(proc_dir,...
    [ datestr(now,'yyyymmdd') '_phcp_' options.which_ROI '_' num2str(numel(c.suj)) ...
    'subj_Cr_scaled' options.output_suffix '.csv']);
if ~exist(write_name,'file')
    write_conc_res_to_csv(c_cr,write_name)
else
    error(['The following file already exists, to create a new version, you must delete the existing one! - ' write_name]);
end

% scale to Water
% first get all tissue fractions
tissue_fract_data = mps_run_all_MRS_tissue_correct;

not_missing_subjs = ~isnan( mean( tissue_fract_data.tissue_fract(...
    :, ROI_idx, :), 3));

cw = c;
if sum(not_missing_subjs) ~= numel(c.suj)
    error('number of subjects in tissue_fract_data does not match data in c!');
else
    cw.fgray = tissue_fract_data.tissue_fract(not_missing_subjs, ROI_idx, 1); % GM first
    cw.fwhite = tissue_fract_data.tissue_fract(not_missing_subjs, ROI_idx, 2); % WM second
    cw.fcsf = tissue_fract_data.tissue_fract(not_missing_subjs, ROI_idx, 3); % CSF third
end

corr_factor = water_content_attenuation(cw, par);
c_wscale = correct_result(cw, corr_factor);

write_name = fullfile(proc_dir,...
    [ datestr(now,'yyyymmdd') '_phcp_' options.which_ROI '_' num2str(numel(c.suj)) ...
    'subj_H2O_scaled' options.output_suffix '.csv']);
if ~exist(write_name,'file')
    write_conc_res_to_csv(c_wscale,write_name)
else
    error(['The following file already exists, to create a new version, you must delete the existing one! - ' write_name]);
end

% rename .pdf and .ps

write_name = fullfile(proc_dir,...
    [datestr(now,'yyyymmdd') '_phcp_' options.which_ROI '_' num2str(numel(c.suj)) ...
    'subj' options.output_suffix '.pdf']);
run_cmd = ['! mv ' proc_dir '/' options.which_ROI '_lcm_fit.pdf ' write_name ' ;'];
eval(run_cmd);

write_name = fullfile(proc_dir,...
    [datestr(now,'yyyymmdd') '_phcp_' options.which_ROI '_' num2str(numel(c.suj)) ...
    'subj' options.output_suffix '.ps']);
run_cmd = ['! mv ' proc_dir '/' options.which_ROI '_lcm_fit.ps ' write_name ' ;'];
eval(run_cmd);

end % options.which_step

%% output
options.par = par;
output.options = options;
output.date_run = datestr(now);

end