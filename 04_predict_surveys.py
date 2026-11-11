from config.surveys import *

for s in Surveys.all():
    # predict values for both survey samples 
    for other in Surveys.all():
        s.write_predictors(survey_sample = other)

        for m in (s.baseline, s.model):
            s.write_predictions(m, survey_sample = other)

    # predict values at the population level
    for year in YEARS:
        s.write_predictors(year = year)
        s.write_predictions(s.model, year = year)
    
    evaluation = s.compute_evaluation()
    s.write_evaluation(evaluation)