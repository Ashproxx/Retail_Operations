# Measured forecasting comparison

Source: **synthetic-workbook**. Independent frozen test run at code `c1e872fd5f331f42010b56a7c3019dd1d597c278`.

Dates reserved: 2026-08-05–2026-09-29. Two h-day blocks begin August 5 and September 2; both use the same pre-test fit. First-block lead is h+1 to 2h, second-block lead h+29 to 2h+28. Model selection used only the first three validation origins. Calibration residuals end no later than the final training cutoff.

Reported values are unweighted averages across eligible series, with each series metric calculated on both scored blocks. They are not volume-weighted chain totals. No model was automatically promoted.

| Level | Model | h | Series | MAE | RMSE | WAPE | MASE | Bias | 80% coverage | 95% coverage | Fit s | Predict s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chain | croston | 1 | 1 | 68.1160 | 68.5277 | 0.3972 | 1.5018 | 68.1160 | 1.0000 | 1.0000 | 0.0002 | 0.0000 |
| chain | croston | 7 | 1 | 74.8606 | 87.6270 | 0.3164 | 1.6398 | -3.5592 | 0.7143 | 0.7857 | 0.0002 | 0.0000 |
| chain | croston | 14 | 1 | 66.7156 | 79.7342 | 0.2866 | 1.4456 | 0.9689 | 0.7143 | 0.8214 | 0.0002 | 0.0000 |
| chain | croston | 28 | 1 | 62.6219 | 73.3734 | 0.2750 | 1.3237 | 8.8627 | 0.7679 | 0.8929 | 0.0002 | 0.0000 |
| chain | ets | 1 | 1 | 18.5807 | 20.0373 | 0.1083 | 0.4096 | 18.5807 | 1.0000 | 1.0000 | 1.1024 | 0.0019 |
| chain | ets | 7 | 1 | 27.3238 | 34.5502 | 0.1155 | 0.5985 | -2.9216 | 0.8571 | 0.9286 | 0.1454 | 0.0022 |
| chain | ets | 14 | 1 | 28.2030 | 35.4855 | 0.1212 | 0.6111 | 5.9958 | 0.8571 | 0.9643 | 0.1313 | 0.0018 |
| chain | ets | 28 | 1 | 31.1311 | 37.9476 | 0.1367 | 0.6580 | -2.3252 | 0.6964 | 0.9821 | 0.1276 | 0.0017 |
| chain | exponential_0.3 | 1 | 1 | 75.7463 | 76.1167 | 0.4417 | 1.6700 | 75.7463 | 1.0000 | 1.0000 | 0.0001 | 0.0000 |
| chain | exponential_0.3 | 7 | 1 | 72.9242 | 88.1627 | 0.3083 | 1.5974 | -10.3369 | 0.7857 | 0.8571 | 0.0001 | 0.0002 |
| chain | exponential_0.3 | 14 | 1 | 64.2411 | 80.0984 | 0.2760 | 1.3919 | -7.6917 | 0.8214 | 0.8214 | 0.0001 | 0.0003 |
| chain | exponential_0.3 | 28 | 1 | 61.2285 | 72.8833 | 0.2689 | 1.2942 | 2.6200 | 0.8750 | 0.9286 | 0.0001 | 0.0006 |
| chain | gamma_poisson | 1 | 1 | 69.9774 | 70.3782 | 0.4080 | 1.5428 | 69.9774 | 1.0000 | 1.0000 | 0.0002 | 0.0000 |
| chain | gamma_poisson | 7 | 1 | 77.2650 | 87.6892 | 0.3266 | 1.6925 | 4.8562 | 0.6429 | 0.7857 | 0.0001 | 0.0000 |
| chain | gamma_poisson | 14 | 1 | 68.9743 | 80.2206 | 0.2963 | 1.4945 | 8.8742 | 0.7143 | 0.7500 | 0.0001 | 0.0000 |
| chain | gamma_poisson | 28 | 1 | 63.9892 | 74.2328 | 0.2810 | 1.3526 | 14.3318 | 0.7679 | 0.8571 | 0.0001 | 0.0000 |
| chain | hist_gradient | 1 | 1 | 20.7864 | 21.2572 | 0.1212 | 0.4583 | 20.7864 | 1.0000 | 1.0000 | 0.0492 | 0.0155 |
| chain | hist_gradient | 7 | 1 | 33.9263 | 42.2309 | 0.1434 | 0.7432 | -7.0715 | 0.7857 | 0.9286 | 0.0482 | 0.0225 |
| chain | hist_gradient | 14 | 1 | 31.4376 | 41.9610 | 0.1350 | 0.6812 | -4.7639 | 0.7857 | 0.8571 | 0.0470 | 0.0276 |
| chain | hist_gradient | 28 | 1 | 33.8184 | 41.5121 | 0.1485 | 0.7148 | -1.8175 | 0.7500 | 0.9286 | 0.0462 | 0.0436 |
| chain | lasso | 1 | 1 | 12.3911 | 13.4077 | 0.0723 | 0.2732 | -5.1211 | 1.0000 | 1.0000 | 0.0099 | 0.0066 |
| chain | lasso | 7 | 1 | 30.1554 | 41.3699 | 0.1275 | 0.6605 | -4.9569 | 0.7857 | 0.9286 | 0.0098 | 0.0082 |
| chain | lasso | 14 | 1 | 32.8524 | 44.4781 | 0.1411 | 0.7118 | -6.2122 | 0.7143 | 0.8929 | 0.0096 | 0.0107 |
| chain | lasso | 28 | 1 | 37.1131 | 47.5307 | 0.1630 | 0.7845 | 2.1386 | 0.5893 | 0.8929 | 0.0099 | 0.0172 |
| chain | moving_average_7 | 1 | 1 | 63.6429 | 64.0833 | 0.3711 | 1.4031 | 63.6429 | 1.0000 | 1.0000 | 0.0001 | 0.0000 |
| chain | moving_average_7 | 7 | 1 | 74.4490 | 87.6973 | 0.3147 | 1.6308 | -5.0000 | 0.6429 | 0.7857 | 0.0001 | 0.0001 |
| chain | moving_average_7 | 14 | 1 | 66.9490 | 79.7483 | 0.2876 | 1.4506 | 1.7857 | 0.7143 | 0.8214 | 0.0001 | 0.0001 |
| chain | moving_average_7 | 28 | 1 | 66.6250 | 76.9667 | 0.2926 | 1.4083 | 24.8750 | 0.6964 | 0.9107 | 0.0001 | 0.0002 |
| chain | naive | 1 | 1 | 26.5000 | 27.5409 | 0.1545 | 0.5842 | 26.5000 | 1.0000 | 1.0000 | 0.0002 | 0.0000 |
| chain | naive | 7 | 1 | 69.4286 | 103.1691 | 0.2935 | 1.5208 | -54.5714 | 0.7857 | 0.8571 | 0.0001 | 0.0000 |
| chain | naive | 14 | 1 | 60.2143 | 90.0147 | 0.2587 | 1.3047 | -41.7857 | 0.8929 | 0.8929 | 0.0001 | 0.0000 |
| chain | naive | 28 | 1 | 69.5179 | 98.0873 | 0.3053 | 1.4694 | -65.6964 | 0.8750 | 0.9286 | 0.0001 | 0.0000 |
| chain | ridge | 1 | 1 | 12.5499 | 14.0091 | 0.0732 | 0.2767 | -6.2254 | 1.0000 | 1.0000 | 0.3348 | 0.0058 |
| chain | ridge | 7 | 1 | 31.0927 | 42.3210 | 0.1314 | 0.6811 | -5.8281 | 0.7857 | 0.9286 | 0.0097 | 0.0084 |
| chain | ridge | 14 | 1 | 33.3369 | 45.0808 | 0.1432 | 0.7223 | -7.4693 | 0.7500 | 0.8929 | 0.0130 | 0.0123 |
| chain | ridge | 28 | 1 | 35.5994 | 46.7105 | 0.1563 | 0.7525 | -0.2738 | 0.6429 | 0.8929 | 0.0093 | 0.0174 |
| chain | sarima | 1 | 1 | 44.6533 | 45.0984 | 0.2604 | 0.9845 | 44.6533 | 1.0000 | 1.0000 | 0.1050 | 0.0017 |
| chain | sarima | 7 | 1 | 51.2870 | 65.3149 | 0.2168 | 1.1234 | -1.7313 | 0.7857 | 0.8571 | 0.0839 | 0.0016 |
| chain | sarima | 14 | 1 | 58.7645 | 71.2398 | 0.2524 | 1.2733 | 5.9955 | 0.5000 | 0.7857 | 0.0946 | 0.0018 |
| chain | sarima | 28 | 1 | 59.8599 | 70.1288 | 0.2629 | 1.2653 | 14.1927 | 0.5000 | 0.7143 | 0.0935 | 0.0020 |
| chain | sba | 1 | 1 | 56.1352 | 56.6340 | 0.3273 | 1.2376 | 56.1352 | 1.0000 | 1.0000 | 0.0002 | 0.0000 |
| chain | sba | 7 | 1 | 71.5319 | 88.8659 | 0.3024 | 1.5669 | -15.2098 | 0.7857 | 0.7857 | 0.0002 | 0.0000 |
| chain | sba | 14 | 1 | 63.5858 | 80.4456 | 0.2732 | 1.3777 | -10.7188 | 0.8214 | 0.8214 | 0.0002 | 0.0000 |
| chain | sba | 28 | 1 | 60.0413 | 72.8965 | 0.2637 | 1.2691 | -2.9652 | 0.8750 | 0.8929 | 0.0002 | 0.0000 |
| chain | seasonal_naive_7 | 1 | 1 | 9.5000 | 12.1037 | 0.0554 | 0.2094 | 9.5000 | 1.0000 | 1.0000 | 0.0001 | 0.0000 |
| chain | seasonal_naive_7 | 7 | 1 | 25.2857 | 32.0936 | 0.1069 | 0.5539 | -5.0000 | 0.9286 | 0.9286 | 0.0001 | 0.0000 |
| chain | seasonal_naive_7 | 14 | 1 | 34.3571 | 42.6933 | 0.1476 | 0.7444 | 1.7857 | 0.6786 | 0.8929 | 0.0001 | 0.0000 |
| chain | seasonal_naive_7 | 28 | 1 | 43.8036 | 50.9487 | 0.1924 | 0.9259 | 24.8750 | 0.4643 | 0.8929 | 0.0002 | 0.0000 |
| chain | tsb | 1 | 1 | 68.1160 | 68.5277 | 0.3972 | 1.5018 | 68.1160 | 1.0000 | 1.0000 | 0.0002 | 0.0000 |
| chain | tsb | 7 | 1 | 74.8606 | 87.6270 | 0.3164 | 1.6398 | -3.5592 | 0.7143 | 0.7857 | 0.0002 | 0.0000 |
| chain | tsb | 14 | 1 | 66.7156 | 79.7342 | 0.2866 | 1.4456 | 0.9689 | 0.7143 | 0.8214 | 0.0002 | 0.0000 |
| chain | tsb | 28 | 1 | 62.6219 | 73.3734 | 0.2750 | 1.3237 | 8.8627 | 0.7679 | 0.8929 | 0.0002 | 0.0000 |
| chain | weekday_mean_28 | 1 | 1 | 17.2500 | 18.8099 | 0.1006 | 0.3803 | 17.2500 | 1.0000 | 1.0000 | 0.0001 | 0.0000 |
| chain | weekday_mean_28 | 7 | 1 | 31.8571 | 38.7047 | 0.1347 | 0.6978 | 1.5714 | 0.5714 | 0.8571 | 0.0001 | 0.0001 |
| chain | weekday_mean_28 | 14 | 1 | 31.0536 | 38.9344 | 0.1334 | 0.6729 | 5.4643 | 0.5000 | 0.8214 | 0.0001 | 0.0002 |
| chain | weekday_mean_28 | 28 | 1 | 30.8839 | 37.9631 | 0.1356 | 0.6528 | -0.6607 | 0.6786 | 0.8571 | 0.0002 | 0.0005 |
| store | croston | 1 | 11 | 4.4154 | 4.8284 | 0.5667 | 0.7187 | 3.6500 | 0.8636 | 1.0000 | 0.0002 | 0.0000 |
| store | croston | 7 | 10 | 6.2062 | 7.7108 | 0.4119 | 0.9526 | -0.9970 | 0.7071 | 0.9500 | 0.0002 | 0.0000 |
| store | croston | 14 | 10 | 5.6230 | 7.0478 | 0.3894 | 0.8592 | -0.2371 | 0.7393 | 0.9321 | 0.0002 | 0.0000 |
| store | croston | 28 | 9 | 5.4944 | 6.7838 | 0.3881 | 0.8220 | 0.3273 | 0.7917 | 0.9663 | 0.0002 | 0.0000 |
| store | ets | 1 | 11 | 3.0388 | 3.5312 | 0.3547 | 0.4922 | 0.1709 | 0.9091 | 1.0000 | 0.0598 | 0.0020 |
| store | ets | 7 | 10 | 4.4516 | 5.4737 | 0.3010 | 0.6913 | -0.9823 | 0.7429 | 0.9571 | 0.0598 | 0.0019 |
| store | ets | 14 | 10 | 4.3049 | 5.3638 | 0.3027 | 0.6638 | -0.2699 | 0.8143 | 0.9571 | 0.0599 | 0.0020 |
| store | ets | 28 | 9 | 4.4683 | 5.5280 | 0.3206 | 0.6750 | 0.3118 | 0.8274 | 0.9663 | 0.0580 | 0.0020 |
| store | exponential_0.3 | 1 | 11 | 4.8090 | 5.2937 | 0.6390 | 0.7868 | 4.3128 | 0.8636 | 1.0000 | 0.0001 | 0.0000 |
| store | exponential_0.3 | 7 | 10 | 6.2831 | 7.8887 | 0.4166 | 0.9642 | -1.5665 | 0.7357 | 0.9500 | 0.0001 | 0.0002 |
| store | exponential_0.3 | 14 | 10 | 5.6746 | 7.2794 | 0.3928 | 0.8670 | -1.0121 | 0.7929 | 0.9250 | 0.0001 | 0.0003 |
| store | exponential_0.3 | 28 | 9 | 5.5414 | 6.9120 | 0.3921 | 0.8300 | 0.1342 | 0.7798 | 0.9603 | 0.0001 | 0.0006 |
| store | gamma_poisson | 1 | 11 | 4.4180 | 4.8981 | 0.5622 | 0.7128 | 3.6025 | 0.8636 | 1.0000 | 0.0001 | 0.0000 |
| store | gamma_poisson | 7 | 10 | 6.2345 | 7.6129 | 0.4142 | 0.9566 | -0.3701 | 0.7214 | 0.9214 | 0.0001 | 0.0000 |
| store | gamma_poisson | 14 | 10 | 5.6716 | 6.9565 | 0.3930 | 0.8666 | 0.3179 | 0.7679 | 0.9321 | 0.0001 | 0.0000 |
| store | gamma_poisson | 28 | 9 | 5.5908 | 6.7997 | 0.3949 | 0.8353 | 0.9526 | 0.8393 | 0.9623 | 0.0001 | 0.0000 |
| store | hist_gradient | 1 | 11 | 3.3320 | 3.8632 | 0.3372 | 0.5327 | -1.2535 | 0.8636 | 1.0000 | 0.0463 | 0.0164 |
| store | hist_gradient | 7 | 10 | 5.2267 | 6.4869 | 0.3511 | 0.8075 | -2.1899 | 0.7643 | 0.9643 | 0.0458 | 0.0228 |
| store | hist_gradient | 14 | 10 | 4.7786 | 6.1151 | 0.3337 | 0.7344 | -1.3019 | 0.8036 | 0.9571 | 0.0455 | 0.0300 |
| store | hist_gradient | 28 | 9 | 4.8461 | 6.0935 | 0.3493 | 0.7341 | -0.9731 | 0.8393 | 0.9623 | 0.0432 | 0.0457 |
| store | lasso | 1 | 11 | 3.2052 | 3.6471 | 0.3438 | 0.5120 | -1.1291 | 0.9091 | 1.0000 | 0.0096 | 0.0068 |
| store | lasso | 7 | 10 | 4.8460 | 6.0729 | 0.3243 | 0.7478 | -1.2899 | 0.7643 | 0.9643 | 0.0093 | 0.0090 |
| store | lasso | 14 | 10 | 4.5109 | 5.7442 | 0.3129 | 0.6908 | -0.7015 | 0.7929 | 0.9571 | 0.0099 | 0.0126 |
| store | lasso | 28 | 9 | 4.5761 | 5.8539 | 0.3254 | 0.6878 | -0.5481 | 0.8115 | 0.9603 | 0.0084 | 0.0175 |
| store | moving_average_7 | 1 | 11 | 4.4286 | 4.7947 | 0.5719 | 0.7241 | 3.5974 | 0.9091 | 1.0000 | 0.0001 | 0.0000 |
| store | moving_average_7 | 7 | 10 | 6.2735 | 7.7890 | 0.4164 | 0.9628 | -1.0714 | 0.7143 | 0.9357 | 0.0001 | 0.0001 |
| store | moving_average_7 | 14 | 10 | 5.6939 | 7.2276 | 0.3945 | 0.8704 | -0.4429 | 0.7643 | 0.9250 | 0.0001 | 0.0001 |
| store | moving_average_7 | 28 | 9 | 5.8180 | 7.0772 | 0.4113 | 0.8710 | 1.4603 | 0.7758 | 0.9544 | 0.0001 | 0.0002 |
| store | naive | 1 | 11 | 4.0000 | 4.4129 | 0.5437 | 0.6601 | 1.6364 | 1.0000 | 1.0000 | 0.0001 | 0.0000 |
| store | naive | 7 | 10 | 7.0286 | 9.0585 | 0.4712 | 1.0901 | -4.1429 | 0.8071 | 0.9643 | 0.0001 | 0.0000 |
| store | naive | 14 | 10 | 6.6571 | 8.4975 | 0.4556 | 1.0085 | -3.0714 | 0.8500 | 0.9429 | 0.0001 | 0.0000 |
| store | naive | 28 | 9 | 6.6865 | 8.6419 | 0.4752 | 1.0074 | -4.0952 | 0.8512 | 0.9623 | 0.0001 | 0.0000 |
| store | ridge | 1 | 11 | 3.2827 | 3.6836 | 0.3520 | 0.5249 | -1.1294 | 0.9091 | 1.0000 | 0.0098 | 0.0066 |
| store | ridge | 7 | 10 | 4.8462 | 6.1007 | 0.3239 | 0.7473 | -1.2948 | 0.7500 | 0.9643 | 0.0097 | 0.0086 |
| store | ridge | 14 | 10 | 4.4969 | 5.7720 | 0.3118 | 0.6886 | -0.7272 | 0.7893 | 0.9643 | 0.0098 | 0.0121 |
| store | ridge | 28 | 9 | 4.5929 | 5.8956 | 0.3268 | 0.6907 | -0.7259 | 0.8155 | 0.9663 | 0.0093 | 0.0173 |
| store | sarima | 1 | 11 | 3.8441 | 4.1982 | 0.4953 | 0.6267 | 3.0569 | 0.9091 | 1.0000 | 0.0541 | 0.0016 |
| store | sarima | 7 | 10 | 6.0891 | 7.4293 | 0.4052 | 0.9354 | -0.3803 | 0.7071 | 0.9357 | 0.0547 | 0.0016 |
| store | sarima | 14 | 10 | 5.6519 | 6.9310 | 0.3918 | 0.8639 | 0.3315 | 0.7500 | 0.9393 | 0.0573 | 0.0018 |
| store | sarima | 28 | 9 | 5.5974 | 6.8037 | 0.3954 | 0.8363 | 0.9940 | 0.7937 | 0.9623 | 0.0629 | 0.0021 |
| store | sarimax_calendar | 1 | 11 | 2.9145 | 3.3580 | 0.3221 | 0.4712 | -0.9308 | 0.9545 | 1.0000 | 0.1372 | 0.0017 |
| store | sarimax_calendar | 7 | 10 | 4.8057 | 6.0119 | 0.3231 | 0.7424 | -0.5381 | 0.8000 | 0.9357 | 0.1314 | 0.0018 |
| store | sarimax_calendar | 14 | 10 | 4.4953 | 5.7287 | 0.3122 | 0.6881 | 0.1283 | 0.8036 | 0.9429 | 0.1334 | 0.0020 |
| store | sarimax_calendar | 28 | 9 | 4.6915 | 5.9352 | 0.3343 | 0.7068 | 0.6414 | 0.8175 | 0.9524 | 0.1263 | 0.0023 |
| store | sba | 1 | 11 | 4.1173 | 4.3810 | 0.5233 | 0.6697 | 2.9357 | 0.9545 | 1.0000 | 0.0002 | 0.0000 |
| store | sba | 7 | 10 | 6.1643 | 7.8186 | 0.4083 | 0.9460 | -1.7093 | 0.6929 | 0.9500 | 0.0002 | 0.0000 |
| store | sba | 14 | 10 | 5.5732 | 7.0846 | 0.3859 | 0.8522 | -0.9538 | 0.7607 | 0.9321 | 0.0002 | 0.0000 |
| store | sba | 28 | 9 | 5.4076 | 6.7828 | 0.3823 | 0.8097 | -0.4049 | 0.7996 | 0.9722 | 0.0002 | 0.0000 |
| store | seasonal_naive_7 | 1 | 11 | 3.9091 | 4.3759 | 0.3971 | 0.6129 | -0.0909 | 0.9091 | 1.0000 | 0.0001 | 0.0000 |
| store | seasonal_naive_7 | 7 | 10 | 5.3429 | 6.6684 | 0.3615 | 0.8294 | -1.0714 | 0.8071 | 0.9714 | 0.0001 | 0.0000 |
| store | seasonal_naive_7 | 14 | 10 | 5.8857 | 7.4486 | 0.4106 | 0.9063 | -0.4429 | 0.8179 | 0.9607 | 0.0001 | 0.0000 |
| store | seasonal_naive_7 | 28 | 9 | 6.1190 | 7.7286 | 0.4451 | 0.9339 | 1.4603 | 0.8313 | 0.9563 | 0.0001 | 0.0000 |
| store | tsb | 1 | 11 | 4.4154 | 4.8284 | 0.5667 | 0.7187 | 3.6500 | 0.8636 | 1.0000 | 0.0002 | 0.0000 |
| store | tsb | 7 | 10 | 6.2062 | 7.7108 | 0.4119 | 0.9526 | -0.9970 | 0.7071 | 0.9500 | 0.0002 | 0.0000 |
| store | tsb | 14 | 10 | 5.6230 | 7.0478 | 0.3894 | 0.8592 | -0.2371 | 0.7393 | 0.9321 | 0.0002 | 0.0000 |
| store | tsb | 28 | 9 | 5.4944 | 6.7838 | 0.3881 | 0.8220 | 0.3273 | 0.7917 | 0.9663 | 0.0002 | 0.0000 |
| store | weekday_mean_28 | 1 | 11 | 3.0227 | 3.5091 | 0.3162 | 0.4823 | 0.0000 | 0.9545 | 1.0000 | 0.0001 | 0.0000 |
| store | weekday_mean_28 | 7 | 10 | 4.6643 | 6.0025 | 0.3146 | 0.7244 | -0.5286 | 0.7857 | 0.9286 | 0.0001 | 0.0001 |
| store | weekday_mean_28 | 14 | 10 | 4.4982 | 5.7097 | 0.3161 | 0.6965 | -0.0286 | 0.8536 | 0.9250 | 0.0001 | 0.0002 |
| store | weekday_mean_28 | 28 | 9 | 4.8304 | 6.1364 | 0.3495 | 0.7350 | -0.3968 | 0.8155 | 0.9444 | 0.0001 | 0.0003 |

## Coverage and failures

{"store": 9, "store_category": 120, "store_sku": 1700}
Validation optimizer/availability failures: 1; final-test failures: 60.

## Frozen selection review

| Series | h | Selected before test | Baseline | Decision |
|---|---:|---|---|---|
| chain / chain | 1 | sarima | seasonal_naive_7 | RETAIN_BASELINE |
| chain / chain | 7 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| chain / chain | 14 | ets | weekday_mean_28 | RETAIN_BASELINE |
| chain / chain | 28 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST01 | 1 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST01 | 7 | hist_gradient | weekday_mean_28 | RETAIN_BASELINE |
| store / ST01 | 14 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST01 | 28 | ridge | weekday_mean_28 | RETAIN_BASELINE |
| store / ST03 | 1 | seasonal_naive_7 | seasonal_naive_7 | RETAIN_BASELINE |
| store / ST03 | 7 | sarimax_calendar | moving_average_7 | UNVERIFIED |
| store / ST03 | 14 | weekday_mean_28 | weekday_mean_28 | UNVERIFIED |
| store / ST03 | 28 | ets | weekday_mean_28 | UNVERIFIED |
| store / ST04 | 1 | gamma_poisson | weekday_mean_28 | RETAIN_BASELINE |
| store / ST04 | 7 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST04 | 14 | ets | moving_average_7 | ELIGIBLE_FOR_REVIEW |
| store / ST04 | 28 | ets | moving_average_7 | RETAIN_BASELINE |
| store / ST05 | 1 | naive | naive | RETAIN_BASELINE |
| store / ST05 | 7 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST05 | 14 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST05 | 28 | hist_gradient | weekday_mean_28 | RETAIN_BASELINE |
| store / ST07 | 1 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST07 | 7 | ets | weekday_mean_28 | ELIGIBLE_FOR_REVIEW |
| store / ST07 | 14 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST07 | 28 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST08 | 1 | seasonal_naive_7 | seasonal_naive_7 | RETAIN_BASELINE |
| store / ST08 | 7 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST08 | 14 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST08 | 28 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST10 | 1 | exponential_0.3 | exponential_0.3 | RETAIN_BASELINE |
| store / ST10 | 7 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST10 | 14 | ets | moving_average_7 | RETAIN_BASELINE |
| store / ST10 | 28 | ridge | weekday_mean_28 | RETAIN_BASELINE |
| store / ST11 | 1 | hist_gradient | exponential_0.3 | RETAIN_BASELINE |
| store / ST11 | 7 | sarimax_calendar | weekday_mean_28 | RETAIN_BASELINE |
| store / ST11 | 14 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST11 | 28 | ridge | weekday_mean_28 | RETAIN_BASELINE |
| store / ST12 | 1 | sarimax_calendar | exponential_0.3 | RETAIN_BASELINE |
| store / ST12 | 7 | exponential_0.3 | exponential_0.3 | RETAIN_BASELINE |
| store / ST12 | 14 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST12 | 28 | sba | exponential_0.3 | ELIGIBLE_FOR_REVIEW |
| store / ST14 | 1 | sarimax_calendar | exponential_0.3 | RETAIN_BASELINE |
| store / ST14 | 7 | ets | weekday_mean_28 | ELIGIBLE_FOR_REVIEW |
| store / ST14 | 14 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST14 | 28 | ets | weekday_mean_28 | RETAIN_BASELINE |
| store / ST15 | 1 | weekday_mean_28 | weekday_mean_28 | RETAIN_BASELINE |
| store / ST15 | 7 | sarima | moving_average_7 | RETAIN_BASELINE |
| store / ST15 | 14 | lasso | weekday_mean_28 | RETAIN_BASELINE |
| store / ST15 | 28 | ets | weekday_mean_28 | UNVERIFIED |

## Limitations

- Synthetic results are not real-world accuracy.
- No causal price/weather claim.
- Weather ablation unavailable without historical forecast vintages.
- Only complete eligible series were scored; no missing days were turned into zero sales.
- Conformal calibration pools leads and temporal dependence weakens exchangeability. Empirical coverage is reported.
- One predefined setting per model, no broad hyperparameter search. Global pooled boosting and feature importance comparisons remain incomplete.
- Block bootstrap concatenates three separated validation windows; significance is exploratory, not a deployment guarantee.
- Quantile boosting is implemented and unit tested but not included in this final comparison. Pinball comparison remains unverified.
- Store/category and store/SKU tables report exclusions rather than invented scores.

## Reproduction

Run validation and test once in a fresh output directory using `python -m scripts.benchmark_forecasting --phase validation` then `--phase test`. The TEST_OPENED marker prevents accidental retuning on the same test. Generate this document with `python -m scripts.forecast_report --input <run-directory>`. Changing models after reading the test requires a new untouched evaluation dataset, not deletion of the marker.
