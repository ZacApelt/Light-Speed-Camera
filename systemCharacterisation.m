data = readmatrix("./scope captures/pure impulse response averaged.csv");

signal = readmatrix("./scope captures/beamdumpvsnobeamdump.csv");

s = signal(:,2);
s2 = signal(:,3);
s = s(:);
s2 = s2(:);
s = -s;
s2 = -s2;
ts = signal(:,1);
ts = ts(:);

t = data(:,1);
y = data(:,2);
t = t(:);
y = y(:);

Ts = median(diff(t));

% Baseline subtract
Nbase = min(5, round(0.1*numel(y)));
y = y - mean(y(1:Nbase));

% Make pulse positive
if abs(min(y)) > abs(max(y))
    y = -y;
end

% Normalise
y = y ./ max(abs(y));

s = s ./ max(abs(s)) + 1;
s2 = s2 ./ max(abs(s2)) + 1;


%na = 4;   % poles
%nb = 7;   % zeros

na = 4;   % poles
nb = 4;   % zeros

[b,a] = prony(y, nb, na);

H = tf(b,a)
%figure(1);
%pzmap(H)
%zgrid
%grid on
%rlocus(H)

hfit = impz(b,a,length(y));

% Check original fitted model stability
poles_H = roots(a);
zeros_H = roots(b);

fprintf("Max pole magnitude H: %.3f\n", max(abs(poles_H)));
fprintf("Max zero magnitude H: %.3f\n", max(abs(zeros_H)));

% Inverse filter poles are zeros of H
if any(abs(zeros_H) >= 1)
    warning("Inverse filter is unstable or marginal because H has zeros outside/on unit circle.");
end

function x_est = inverse_filter_regularised(y, b, a, lambda)
    % y = measured signal
    % H(z) = b/a
    % regularised inverse in frequency domain:
    % X = Y * conj(H) / (abs(H)^2 + lambda)

    y = y(:);
    N = length(y);
    Nfft = 2^nextpow2(4*N);

    [H, ~] = freqz(b, a, Nfft, 'whole');

    Y = fft(y, Nfft);

    X = Y .* conj(H) ./ (abs(H).^2 + lambda);

    x_full = real(ifft(X));
    x_est = x_full(1:N);
end

lambda = 0.1;
x_est = inverse_filter_regularised(s, b, a, lambda);
x_est2 = inverse_filter_regularised(s2, b, a, lambda);

%{
figure(2);
plot(t,y,'o')
hold on
plot(t,hfit)
plot(ts,x_est)
%}

figure(3);
hold on;
plot(ts, s);
plot(ts, s2);
plot(ts, x_est.*2);
plot(ts, x_est2.*2);
ax = gca;
ax.XAxis.Exponent = -9; 
grid on
