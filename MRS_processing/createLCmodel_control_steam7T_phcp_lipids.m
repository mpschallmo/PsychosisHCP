function controlfilename = createLCmodel_control_steam7T_phcp_lipids(metabname,l1,l2,l3,preproc_dir)
% useage: controlfilename = createLCmodel_control_steam7T_phcp_lipids(metabname,l1,l2,l3,preproc_dir)
%
% N.B. paths have been removed, labed by ****, must be replaced to match local directories
%
% mps 20230508

do_water_scaling=1;
doecc=0;
TEMET=0;

basis_set_file_path = '**** PATH TO BASIS FILE GOES HERE ****/steam7T_8ms_15Dec2016_Young.BASIS';
% steam7T_8ms_15Dec2016_Young.BASIS used for young data
% from: Marjanska et al. (2017) "REGION-SPECIFIC AGING OF THE HUMAN BRAIN AS EVIDENCED
% BY NEUROCHEMICAL PROFILES MEASURED NONINVASIVELY IN
% THE POSTERIOR CINGULATE CORTEX AND THE OCCIPITAL LOBE
% USING 1H MAGNETIC RESONANCE SPECTROSCOPY AT 7 T"
% Neuroscience, 354, p. 168-177.
% To request this basis set file, please reach out to the
% corresponding author: gosia@cmrr.umn.edu (M. Marjanska)

[pathstr,filename ] = fileparts(metabname)

wd = fullfile(pathstr,preproc_dir)
if ~exist(wd)
  mkdir(wd)
end

rawname = metabname;
metabname = fullfile(wd,filename);

controlfilename=[metabname '.CONTROL'];

% create .CONTROL file for LCModel
disp(['Creating file ' metabname]); disp(' ')



fileid=fopen(controlfilename,'w');
fprintf(fileid,' $LCMODL\n');
fprintf(fileid,[' TITLE=''' metabname '''\n']);
fprintf(fileid,[' OWNER=''CMRR''\n']);
fprintf(fileid,[' PGNORM=''US''\n']);

fprintf(fileid,[' FILBAS=''%s''\n'],basis_set_file_path);

fprintf(fileid,[' FILRAW=''' rawname '.RAW''\n']);
fprintf(fileid,[' FILPS=''' metabname  '.PS''\n']);
fprintf(fileid,[' FILCOO=''' metabname '.COORD''\n']);
fprintf(fileid,' LCOORD=31\n');
fprintf(fileid,[' FILPRI=''' metabname '.PRINT''\n']);
fprintf(fileid,' LPRINT=6\n');


fprintf(fileid,' NAMREL=''Cr''\n'); %gives ratio to tCr
fprintf(fileid,' CONREL=8\n'); %tCr is assumed to be 8 mM

if do_water_scaling
  
  fprintf(fileid,' DOWS=T\n');
  
  dd=dir([rawname,'_ref.H2O']);
  rawname
  if length(dd)~=1
    error('can not find water reference scan of %s',rawname)
    
  end

  fprintf(fileid,' WCONC=55555\n'); 
  fprintf(fileid,' ATTH2O=1\n');
  fprintf(fileid,' ATTMET=1\n');
  
  
    fprintf(fileid,' WSMET=''NAA''\n');
    fprintf(fileid,' WSPPM=2.01\n');
    fprintf(fileid,' N1HMET=3\n');
  
  fprintf(fileid,[' FILH2O=''' fullfile(pathstr,dd.name) '''\n']);

  if doecc
    fprintf(fileid,' DOECC=T\n');
  end
  

end



 fprintf(fileid,' NCOMBI=6\n');
 fprintf(fileid,' CHCOMB(1) = ''NAA+NAAG''\n ');
 fprintf(fileid,' CHCOMB(2) = ''Glu+Gln''\n ');
 fprintf(fileid,' CHCOMB(3) = ''GPC+PCho''\n ');
 fprintf(fileid,' CHCOMB(4) = ''Cr+PCr''\n ');
 fprintf(fileid,' CHCOMB(5) = ''Glc+Tau''\n ');
 fprintf(fileid,' CHCOMB(6) = ''GPC+PCho+PE''\n ');
  
 fprintf(fileid,' NUSE1=5\n');
 fprintf(fileid,' CHUSE1(1)=''NAA''\n');
 fprintf(fileid,' CHUSE1(2)=''Cr''\n');
 fprintf(fileid,' CHUSE1(3)=''PCr''\n');
 fprintf(fileid,' CHUSE1(4)=''Ins''\n');
 fprintf(fileid,' CHUSE1(5)=''Glu''\n');
  
 fprintf(fileid,' NOMIT=5\n');
 fprintf(fileid,' CHOMIT(1)=''bHB''\n');
 fprintf(fileid,' CHOMIT(4)=''Gly''\n');
 fprintf(fileid,' CHOMIT(2)=''Ser''\n');
 fprintf(fileid,' CHOMIT(3)=''Cho''\n');
 fprintf(fileid,' CHOMIT(5)=''Ala''\n');
 
 fprintf(fileid,' NCALIB=0\n');
 fprintf(fileid,' DESDSH=0.002\n');
 fprintf(fileid,' NSDSH=3\n');
 fprintf(fileid,' CHSDSH(1)=''Scyllo''\n');
 fprintf(fileid,' CHSDSH(2)=''GPC''\n');
 fprintf(fileid,' CHSDSH(3)=''Gly''\n');
 fprintf(fileid,' CHSDSH(4)=''bHB''\n');
 fprintf(fileid,' CHSDSH(5)=''Ser''\n');
 fprintf(fileid,' ALSDSH(1)=0.004\n');
 fprintf(fileid,' ALSDSH(2)=0.004\n');
 fprintf(fileid,' ALSDSH(3)=0.004\n');
 fprintf(fileid,' ALSDSH(4)=0.004\n');
 fprintf(fileid,' ALSDSH(5)=0.004\n');
  
 fprintf(fileid,' NEACH=99\n');
 fprintf(fileid,' NAMEAC(1)=''Mac''\n');
 fprintf(fileid,' NAMEAC(2)=''GSH''\n');
 fprintf(fileid,' NAMEAC(3)=''Asc''\n');
 fprintf(fileid,' NAMEAC(4)=''GABA''\n');
 fprintf(fileid,' NAMEAC(5)=''Glu''\n');
 fprintf(fileid,' NAMEAC(6)=''Gln''\n');
 fprintf(fileid,' NAMEAC(7)=''NAA''\n');
 fprintf(fileid,' NAMEAC(8)=''Ins''\n');
 fprintf(fileid,' NAMEAC(9)=''Scyllo''\n');
 fprintf(fileid,' NAMEAC(10)=''Glc''\n');
 fprintf(fileid,' NAMEAC(11)=''Tau''\n');
 fprintf(fileid,' NAMEAC(12)=''Lac''\n');
 fprintf(fileid,' NAMEAC(13)=''PE''\n');
 fprintf(fileid,' NAMEAC(14)=''Asp''\n');
 fprintf(fileid,' NAMEAC(15)=''NAAG''\n');

fprintf(fileid,[' DEGZER= 0.00 \n']); %expected value of zero order phase corection
fprintf(fileid,' SDDEGZ=20.00\n');    %freedom in zero order phase corection
fprintf(fileid,[' DEGPPM=0.00\n']);   %expected value of first order phase correction
fprintf(fileid,' SDDEGP=6.00\n');  %standard deviation in expectation value of degppm 
fprintf(fileid,' SHIFMN=-0.2,-0.1\n');
fprintf(fileid,' SHIFMX=0.3,0.3\n');

fprintf(fileid,' NRATIO=0\n');

fprintf(fileid,' FWHMBA=0.00673\n');
fprintf(fileid,' RFWHM=1.8\n');
fprintf(fileid,' DKNTMN=5\n');

fprintf(fileid,' PPMST=4.1\n');
fprintf(fileid,' PPMEND=0.5\n');


fprintf(fileid,' NSIMUL=7\n');
fprintf(fileid,' CHSIMU(6)= ''Lip165@ 1.65 +- .03 FWHM= .10 < .2 +- .02 AMP= 2.''\n');
fprintf(fileid,' CHSIMU(7)= ''Lip18n@ 1.8 +- .05 FWHM= .15 < .2 +- .035 AMP= -1.''\n');


fprintf(fileid,'CHKEEP=0\n');

fprintf(fileid,[l1,'\n']);
fprintf(fileid,[l2,'\n']);
fprintf(fileid,[l3,'\n']);
fprintf(fileid,' $END\n');

fclose(fileid);

