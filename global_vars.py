""" Define global variables for use in other codes """


label_mappings = {
    # Old Snapshot Serengeti (S1-6) label mapping
    'old_ser_label_mapping': {
         'AARDVARK': 0, 'AARDWOLF': 1, 'BABOON': 2,
         'BATEAREDFOX': 3, 'BUFFALO': 4, 'BUSHBUCK': 5, 'CARACAL': 6,
         'CHEETAH': 7,
         'CIVET': 8, 'DIKDIK': 9, 'ELAND': 10, 'ELEPHANT': 11,
         'GAZELLEGRANTS': 12, 'GAZELLETHOMSONS': 13, 'GENET': 14,
         'GIRAFFE': 15,
         'GUINEAFOWL': 16, 'HARE': 17, 'HARTEBEEST': 18,
         'HIPPOPOTAMUS': 19,
         'HONEYBADGER': 20, 'HUMAN': 21, 'HYENASPOTTED': 22,
         'HYENASTRIPED': 23,
         'IMPALA': 24, 'JACKAL': 25, 'KORIBUSTARD': 26, 'LEOPARD': 27,
         'LIONFEMALE': 28, 'LIONMALE': 29, 'MONGOOSE': 30, 'OSTRICH': 31,
         'BIRDOTHER': 32, 'PORCUPINE': 33, 'REEDBUCK': 34, 'REPTILES': 35,
         'RHINOCEROS': 36, 'RODENTS': 37, 'SECRETARYBIRD': 38, 'SERVAL': 39,
         'TOPI': 40, 'MONKEYVERVET': 41, 'WARTHOG': 42, 'WATERBUCK': 43,
         'WILDCAT': 44, 'WILDEBEEST': 45, 'ZEBRA': 46, 'ZORILLA': 47},
    'counts_to_numeric': {"1": 0, "2": 1, "3": 2, "4": 3,
                          "5": 4, "6": 5, "7": 6, "8": 7, "9": 8,
                          "10": 9, "1150": 10, "51": 11},
    'counts_db_to_ml': {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
                        "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
                        "10": "10", "11": "11-50", "1150": "11-50", "51": "51+"}
}
