function varargout = write_fid_to_lcRAW(fids,par,fidwater);

% n.b. this is a slightly modified version of a function from the matspec toolbox, edited to output file names slightly differently

if ~exist('par'), par='';end

if ~isfield(par,'root_dir'), par.root_dir = '' ;  end
if ~isfield(par,'subdir'), par.subdir = 0;  end
if ~isfield(par,'gessfile'), par.gessfile = 1;  end
if ~isfield(par,'water_ref'), par.water_ref = 0;  end
if ~isfield(par,'filename'),par.filename='guess_from_sujet_name_examnumber_SerDescr'; end
if ~isfield(par,'mega_type'), par.mega_type = 'diff' ;  end %'diff' 'diff_inv' 'first' 'second' 'sum' 'mean'
if ~isfield(par,'TRAMP'), par.TRAMP = 1 ;  end 
if ~isfield(par,'write_volume'), par.write_volume = 0 ;  end 

%if ~isfield(par,''), par. = ;  end

if nargin==0
  varargout{1}=par;
  return
end

if isempty(par.root_dir)
  par.root_dir = spm_select(1,'dir','select a dir to save raw file in','',pwd)
end


for nbser = 1:length(fids)

  if par.write_volume
    VOL =  prod(fids(nbser).Pos.VoiFOV)/1000;
  else
    VOL=1;
  end
  

  if par.subdir
    %make subdir for suj name
    switch par.subdir
      case 3
	serDescr =  fids(nbser).SerDescr;
	if findstr(serDescr,'BG')
	  aaa='BG';
	elseif findstr(serDescr,'CER')
	  aaa='CER';
	elseif findstr(serDescr,'OCC')
	  aaa='OCC';
	elseif findstr(serDescr,'MC')
	  aaa='MC';
	else
	  aaa=serDescr;
	end
	
	suj_dir = fullfile(par.root_dir,aaa);

      case 2
	suj_dir = fullfile(par.root_dir,['Sub' fids(nbser).SubjectID(1:2)]);
      case 1
	suj_dir = fullfile(par.root_dir,fids(nbser).sujet_name);
    end
    
    if ~exist(suj_dir)
      mkdir(suj_dir)
    end
  else
    suj_dir = par.root_dir;
  end

  cenfreq    = fids(nbser).spectrum.cenfreq;	% center frequency of acquisition in Hz
  np         = fids(nbser).spectrum.np;		% number of points
  dw         = fids(nbser).spectrum.dw;		% dwell time	

  
  if findstr(fids(nbser).seqname,'mega')
    fid = fids(nbser).fid;  
    ns = size(fid,2)/2;
  
    fid1 = fid(:,1:ns);
    fid2 = fid(:,(ns+1):end);
    fid1m = mean(fid1,2);
    fid2m = mean(fid2,2);
  
    switch par.mega_type
      case 'diff'
	fid_lc = fid2m - fid1m;
      case 'diff_inv'
	fid_lc = fid1m - fid2m;
	fprintf('INVVVV\n')
      case 'first'
	fid_lc = fid1m;
      case 'second'
	fid_lc = fid2m;
      case 'sum'
	fid_lc = fid1m + fid2m;
      case 'mean'
	fid_lc = (fid1m + fid2m) / 2;
    end

  else
    fid = fids(nbser).fid;
    fid_lc = mean(fid,2);
  end

  dif_fid = [real(fid_lc) imag(fid_lc)];
      
  rp=0;		% zero order phase correction - LCModel
  lp=0;		% first order phase correction - LCModel
  
  if par.gessfile

    if par.gessfile==2
      fname = [fids(nbser).sujet_name];
    elseif par.gessfile==3
      fname = ['Suj' fids(nbser).SubjectID '_' fids(nbser).ser_dir '_NEX' num2str(fids(nbser).Nex)];
    elseif par.gessfile==4
      fname = fids(nbser).ser_dir;
      % added by Gosia for 7 T AS antiox study -- copied into this code by
      % mps on 20180827 in order to produce cleaner file names for pHCP
    elseif par.gessfile==5
       fname = [fids(nbser).sujet_name '_' fids(nbser).SerDescr];
    else
     % fname = [fids(nbser).sujet_name,' ',fids(nbser).examnumber,' ',fids(nbser).SerDescr];
       fname = [fids(nbser).sujet_name,' ',fids(nbser).Serie_description];
    end
    
    switch par.mega_type
%      case 'diff'
%	
%      case 'diff_inv'
%	fname = [fname,'_MEGA_inv'];
      case 'first'
	fname = [fname,'_MEGA_no_edit'];
%      case 'second'
%	fname = [fname,'_MEGA_edit']
%      case 'sum'
%	fname = [fname,'_MEGA_sum']
%      case 'mean'
%	fname = [fname,'_MEGA_mean']	
    end
 
    file_name = nettoie_dir(fname);

    if par.water_ref
      filename = fullfile(suj_dir,[file_name,'.H2O']);
    else
      filename = fullfile(suj_dir,file_name);
    end
    
  else
    filename = par.filename;
  end
  
  createrawfile_mm_3T_CENIR(filename,dif_fid,cenfreq,np,dw,rp,lp,par.TRAMP,VOL);

  if exist('fidwater')
    pp=par;
    pp.gessfile = 0;
    pp.filename = [filename,'_ref.H2O'];
    pp.mega_type = 'mean';
    pp.TRAMP=1;
    
    write_fid_to_lcRAW(fidwater(nbser),pp);
    
  end

  if isfield(fids(nbser),'water_ref')
    pp=par;
    pp.gessfile = 0;
    pp.filename = [filename,'_ref.H2O'];
    pp.mega_type = 'mean';
    pp.TRAMP=1;
    
    write_fid_to_lcRAW(fids(nbser).water_ref,pp);
 
  end
  
end
