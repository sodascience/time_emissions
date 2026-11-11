from config.surveys import *

for s in Surveys.all():
    responses_df = s.compute_responses()
    s.write_responses(responses_df)
    s.write_predictors(survey_sample = s)

    for m in (s.baseline, s.model):
        if m.is_tunable:
            params_tuned = s.tune(m, n_trials = 100, visualize = True)
            s.write_params(m, params_tuned)

        fitted_pipeline = s.train(m)
        s.write_model(fitted_pipeline, m)
        
        s.write_predictions(m, survey_sample = s)
    
    evaluation = s.compute_evaluation()
    s.write_evaluation(evaluation)