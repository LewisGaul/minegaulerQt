from DO_NOT_EDIT import make_module

encrypted_file_source = 'gAAAAABZ7NCWexEUcNWEBQqbX7dpeat9RoWcEH3DzKvcJdgMyiVrTP2TIkaNfr5541dIoYozx5dyEhlRyhclDjhdmE0Q0P5l4SOBS6_3D9Mjl5aLUENdeBNidDSrsHnYpGou5ZpQgOuKztH4CJ1o27fZA2Wb1fJg6JLYx8j7RPexfmvktZztORAzhFH4lBr8X9zqH8FZwOYn_6u8V202TJw2o8W9gmD_FMpvMMzdvwZeIA4BAYnAhMt-m5Z171ZopqIOzmxdExZfeUvOnJ8wr_L8CCvOz9xjmR1N03qU10zejgYwdt4UiT6e45OIJ8qdy9389k6a8-U4C70Qq5gEWXiXiOqm3LbuW7LFn54Rjh_MmAfMcR4TBSCVIJUTB9-omagoV1_apId0KyXBEXIDSbwg9I71EAU9JPGaOjKI1ErgSGGA9n3PBROIky2HZIexnExykOjWz_UdI2rCIVv1UGGATNs7qNcSk8XnpraZU9O7I7Qwr7mYaj0Gqupvz0qgcAl4Vddlq9PCmb1SkK3JoIjAtGvbTkrHbXPmXzfa5hWgQKxPdyJcoKhITN44n3EW9TR4i_LAFlWj5PtcGqT0OqmGFFWo-gjkz_fWznmPk3lNGYDxsAxeIaXZePTP67CL_mHTtpVlrsaBoNklB-rGxlFYKRu0cDpddZjQqKy4WZGSosFI8SP8-bj40n3d0cAM-Fh2zjvjTp6v7BP-q8RhwgDBBcPpH51DzzFC_qXXfw6fyv_ESZHKoTqGJYAf6ac_NgenKDSekRr0H9TMXqyBWhQF-9PzyGDGpZnZSAtT_QBNlUfOcrJCgZEq0zPKDMmSett6WTgRoAzE6XiQjzR9DikFgLoh-JgtbsN_BUamtqHDH3ulhfAa_KeueF5YoFj2jcyzcgbWjVQ_GtND0Mf52Z2Lx38sxjlgbKOcw1ZltoC1ndLPdK2Uq6riAfZmgCiuQmywcfegYZsR839IZucqPrMjyGC_i4GKaO8HfFQHJvxmcsmnvv68TOjxfanVDUoRPhjmnN4IJI_WvkcxNYULXIQB3mEjkKx2y-2qU-59pJpSKnK5TFG8WcWtOfRwtqFIPFEYy1_bevhisoLuxKBsx_1KOIvAsxgZmSzyk7DcNjpsFRFaB3jqEIOvmmRNwUf_9PByg6JyJ2fIAyGiqnkq2DBlJ92t56RdH6OeYr3dh0-rvrB1WXj7De3z3V6RfQQT8ZAXr2rAI8NKHDC6WK40K8ZaKaeerIiErQ==' #to be filled in dynamically

this_module = make_module(encrypted_file_source, globals())

globals().update(this_module.__dict__)

del make_module, encrypted_file_source, this_module