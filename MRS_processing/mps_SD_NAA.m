function [SD_NAA] = mps_SD_NAA(data_struct,param,options)
% usage: [SD_NAA] = mps_SD_NAA(data_struct,options)
%
% n.b. this uses pieces of code originally from the matspec toolbox
%
% mps 2018.10.15
%%

% copying pieces from plot_spectrum.m
spec = data_struct.spectrum;
resolution1 = spec.spectral_widht/(spec.n_data_points-1)/spec.synthesizer_frequency;
freqat0ppm1 = spec.FreqAt0/spec.synthesizer_frequency+spec.ppm_center;
Fppm =  freqat0ppm1:-resolution1:freqat0ppm1-(spec.n_data_points-1)*resolution1;

fid = data_struct.fid;

if (param.mean_line_broadening)
    t=[0:spec.dw:(spec.np-1)*spec.dw]';
    for k=1:size(fid,2)
        fid(:,k) = fid(:,k) .* exp(-t*pi*param.mean_line_broadening);
    end
end
    
all_data = real(fftshift(fft(fid),1));

% plot(Fppm,all_data,'g') % plot to make sure we know what we're looking at
NAA_range = [1.95 2.05];
NAA_idx = find(NAA_range(1) < Fppm & Fppm < NAA_range(2));
[~, NAA_peaks] = max(all_data(NAA_idx,:),[],1); 
NAA_peaks = Fppm(NAA_idx(NAA_peaks));
SD_NAA = std(NAA_peaks,0,2);

end