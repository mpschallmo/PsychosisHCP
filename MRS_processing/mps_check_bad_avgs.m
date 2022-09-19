function mps_check_bad_avgs(f_input, subj_idx, param, plot_bad)
% usage: mps_check_bad_avgs(f_input, subj_idx, param, plot_bad)
%
% n.b. this uses pieces of code originally from the matspec toolbox
%
% author: mps

if ~exist('param','var'), param=[];end

if ~isfield(param,'mean_line_broadening'),  param.mean_line_broadening = 0;end

if ~exist('plot_bad','var'), plot_bad=[];end
%%

spec = f_input.spectrum;
resolution1 = spec.spectral_widht/(spec.n_data_points-1)/spec.synthesizer_frequency;
freqat0ppm1 = spec.FreqAt0/spec.synthesizer_frequency+spec.ppm_center;
Fppm =  freqat0ppm1:-resolution1:freqat0ppm1-(spec.n_data_points-1)*resolution1;

if isfield(param,'x_freq')
    resolution1 = spec.spectral_widht/(spec.n_data_points-1);
    Fppm = spec.FreqAt0:-resolution1: (spec.FreqAt0 - (spec.n_data_points-1)*resolution1);
end

figure; hold on;

fid = f_input(subj_idx).fid;

if (param.mean_line_broadening)
    t=[0:spec.dw:(spec.np-1)*spec.dw]';
    for k=1:size(fid,2)
        fid(:,k) = fid(:,k) .* exp(-t*pi*param.mean_line_broadening);
    end
end

test = real(fftshift(fft(fid),1));

for iAvg = 1:size(test,2)    
    plot3(Fppm,test(:,iAvg),iAvg*ones(1,size(test,1)),'g-','linewidth',0.5);
end
%    plot3(Fppm,test(:,iAvg),iAvg*ones(1,size(test,1)),'b-','linewidth',0.5);
if ~isempty(plot_bad)
    for iAvg = 1:numel(plot_bad)
        plot3(Fppm,test(:,plot_bad(iAvg)),plot_bad(iAvg)*ones(1,size(test,1)),...
            'r-','linewidth',0.5);
    end
end

set(gca,'Xdir','reverse','Xlim',[0 9],'XColor','k','YColor','k',...
    'fontsize',18,'YTick',[]);
set(gcf,'color','w')
box off
ax = axis;
axis([0 5 ax(3) ax(4)])
xlabel('Freq. (ppm)','color','k','fontsize',18)

% look at z-value of the bad averages in the plot...

end