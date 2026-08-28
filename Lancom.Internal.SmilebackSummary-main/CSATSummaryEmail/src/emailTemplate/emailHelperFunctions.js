import {calculateFacesPercentages, calculateNetCsatScore, processComments, calculateIndividualCsatScores,
calculateIndividualFacesPercentages,
calculateTopThreeAgents, bestWorstFiveCompanies, calculateTopThreeCommenters } from "../dataProcessingHelpers.js";

/**
 * replaces the scores in the email template
 * @param {String} template, type = "Weekly" or "Monthly"
 * @param {Object} reviews 
 * @returns {String} template
 */
function _replaceCsatScores(template, reviews, type) {
    const lancomCsatScore = calculateNetCsatScore(reviews);
    const output = _individualScoreTemplate(reviews);
    template = template
        .replace(`{{lancom${type}CsatScore}}`, lancomCsatScore["score"] + `% (${lancomCsatScore["total"]} reviews)`)
        .replace(`{{individual${type}Scores}}`, output);
    return template;
}

/**
 * replaces the feedback in the email template
 * @param {String} template 
 * @param {Object} reviews 
 * @returns {String} template
 */
function _replaceWeeklyFeedback(template, reviews) {
    const sortedComments = processComments(reviews);
    template = _replaceComment(template, sortedComments, "positive");
    template = _replaceComment(template, sortedComments, "neutral");
    template = _replaceComment(template, sortedComments, "negative");
    return template;
}

/**
 * replaces a comment in the email template based on positive, neutral or negative sentiment
 * @param {*} template - string 
 * @param {*} comments - positive: [{}], negative: [{}], neutral: [{}]. list of dicts.
 * @param {*} sentiment - String - positive, neutral or negative
 * @returns String - template
 */
function _replaceComment(template, comments, sentiment) {
    const randomPositiveIndex = Math.floor(Math.random() * (comments[sentiment].length - 1));
    if (comments[sentiment].length === 0) {
        template = template
            .replace(`{{${sentiment}Comment}}`, `Good Job! No ${sentiment} comments.`)
            .replace(`{{${sentiment}CommentEngineer}}`, "")
            .replace(`{{${sentiment}CommenterName}}`, "")
            .replace(`{{${sentiment}CompanyName}}`, "");
        return template;
    }
    const comment = comments[sentiment][randomPositiveIndex]["comment"];
    const commentAgents = comments[sentiment][randomPositiveIndex]["agents"].join(", ");
    const commenterName = comments[sentiment][randomPositiveIndex]["name"];
    const companyName = comments[sentiment][randomPositiveIndex]["company"];
    template = template
        .replace(`{{${sentiment}Comment}}`, comment)
        .replace(`{{${sentiment}CommentEngineer}}`, commentAgents)
        .replace(`{{${sentiment}CommenterName}}`, commenterName)
        .replace(`{{${sentiment}CompanyName}}`, companyName);
    return template;
}

/**
 * Creates template of individual scores in html format in a table
 * @param {Object} reviews 
 * @returns {string} 
 */
function _individualScoreTemplate(reviews) {
    const individualCsatScores = calculateIndividualCsatScores(reviews);
    const individualScores = calculateIndividualFacesPercentages(reviews);
    let output = "";
    const sortedCsatScores = Object.entries(individualCsatScores)
        .sort((a, b) => b[1]["score"] - a[1]["score"] || b[1]["total"] - a[1]["total"]); 
    for (let [name, {score, total}] of sortedCsatScores) {
        const rowTemplate = "<tr><th><strong>{{name}}</strong></th><td>{{positive}}%</td><td>{{neutral}}%</td><td>{{negative}}%</td><td>{{total}}</td><td><strong>{{score}}</strong></td></tr>";
        let row = rowTemplate
            .replace("{{name}}", name)
            .replace("{{score}}", score)
            .replace("{{positive}}", individualScores[name]["positive"])
            .replace("{{neutral}}", individualScores[name]["neutral"])
            .replace("{{negative}}", individualScores[name]["negative"])
            .replace("{{total}}", total);
        output += row + "\n";
    }
    return output;
}

/**
 * replaces the lancom ratings in the email template
 * @param {String} template, type - "Weekly" or "Monthly"
 * @param {Object} reviews 
 * @returns {String} template
 */
function _replaceLancomRatings(template, reviews, type) {
    const lancomRatings = calculateFacesPercentages(reviews); 
    template = template
        .replace(`{{positive${type}Rating}}`, lancomRatings["positive"]["score"] + `% (${lancomRatings["positive"]["total"]} reviews)`)
        .replace(`{{neutral${type}Rating}}`, lancomRatings["neutral"]["score"] + `% (${lancomRatings["neutral"]["total"]} reviews)`)
        .replace(`{{negative${type}Rating}}`, lancomRatings["negative"]["score"] + `% (${lancomRatings["negative"]["total"]} reviews)`);
    return template;
}


/**
 * replaces the top 3 agents in the email template based on CSAT Score and number of reviews
 * @param {String} template 
 * @param {Object} monthlyReviews - JSON Object 
 * @returns {String} template
 */
function _replaceTopThreeAgents(template, monthlyReviews) {
    const rowTemplate = "<tr><th>{{rank}}</th><td>{{name}}</td><td>{{score}}%</td><td>{{reviews}}</td></tr>";
    let output = "";
    const top3 = calculateTopThreeAgents(monthlyReviews);
    for (let i=0; i < top3.length; i++) {
        let data = rowTemplate;
        let name = top3[i][0];
        let score = top3[i][1]["score"];
        let reviews = top3[i][1]["total"]
        let rank = i + 1;
        data = data
            .replace("{{rank}}", rank)
            .replace("{{name}}", name)
            .replace("{{score}}", score)
            .replace("{{reviews}}", reviews);
        output += data + "\n";
    }
    template = template.replace("{{topThree}}", output);
    return template;
}

/**
 * Replaces the date in the template
 * @param {String} template 
 * @returns 
 */
function _replaceDate(template) {
    const date = new Date();
    template = template.replace("{{date}}", date.toDateString());
    return template;
}

/**
 * Replaces the best and worst companies in the email template
 * @param {String} template 
 * @param {Object} reviews JSON object
 * @returns {String} template
 */
function _replaceCompanies(template, reviews) {
    let output = "";
    const companies = bestWorstFiveCompanies(reviews);
    const rowTemplate = "<tr><td>{{name}}</td><td>{{score}}</td><td>{{total}}</td></tr>";

    for (let rank of Object.entries(companies)) {
        for (let company of Object.entries(rank[1])) {
            let row = rowTemplate
                .replace("{{name}}", company[0])  
                .replace("{{score}}", company[1]["score"])  
                .replace("{{total}}", company[1]["total"]);  
            output += row + "\n";
        }
        output += '<tr><th colspan="3">Worst</th></tr>';
    }
    const headingLength = '<tr><th colspan="3">Worst</th></tr>'.length;
    template = template.replace("{{clientScores}}", output.slice(0, -headingLength)); // removes worst heading added by the loop.
    return template;
}

/**
 * creates the string to replace the top three reviewers in the email template
 * @param {{String: String, Integer}} topThree 
 * @returns {String}
 */
function _topCommentersTemplate(topThree) {
    const template = "{{name}} ({{total}} reviews), ";
    let output = "";
    for (let reviewer of topThree) {
        let row = template.replace("{{name}}", reviewer["name"]).replace("{{total}}", reviewer["total"]);
        output += row;
    }
    return output;
}

/**
 * Replaces the top three reviewers in the email template
 * @param {String} template 
 * @param {Object} reviews 
 * @returns {String} template 
 */
function _replaceTopThreeReviewers(template, reviews) {
    const sortedReviews = calculateTopThreeCommenters(reviews);
    const topThreePositive = sortedReviews["positive"];
    const topThreeNeutral = sortedReviews["neutral"];
    const topThreeNegative = sortedReviews["negative"];
    const topThreePositiveRow = _topCommentersTemplate(topThreePositive);
    const topThreeNeutralRow = _topCommentersTemplate(topThreeNeutral);
    const topThreeNegativeRow = _topCommentersTemplate(topThreeNegative);
    template = template
        .replace("{{topThreePositive}}", topThreePositiveRow)
        .replace("{{topThreeNeutral}}", topThreeNeutralRow)
        .replace("{{topThreeNegative}}", topThreeNegativeRow);
    return template;
}

/**
 * Replaces the monthly comments in the email template
 * @param {String} template 
 * @param {Object} reviews - JSON object
 * @returns {String} template
 */
function _replaceMonthlyComments(template, reviews) {
    const sortedComments = processComments(reviews);
    // checks if there are no positive comments 
    if (sortedComments["positive"].length === 0) {
        template = template
            .replace("{{positiveComment}}", "No positive comments")
            .replace("{{positiveCommentName}}", "")
            .replace("{{positiveCommentCompany}}", "")
            .replace("{{positiveCommentEngineer}}", "");
    }
    const positiveComment = sortedComments["positive"][0];
    template = template
        .replace("{{positiveComment}}", positiveComment["comment"])
        .replace("{{positiveCommentName}}", positiveComment["name"])
        .replace("{{positiveCommentCompany}}", positiveComment["company"])
        .replace("{{positiveCommentEngineer}}", positiveComment["agents"]);
    let rowTemplate = "<tr><td>{{comment}}</td><td>{{commenterName}}</td><td>{{companyName}}</td><td>{{engineer}}</td></tr>";
        
    for (let sentiment of ["neutral", "negative"]) {
        let output = "";
        if (sortedComments[sentiment].length === 0) {
            let row = rowTemplate;
            row = row
                .replace(`{{Comment}}`, `Good job! No ${sentiment} comments`)
                .replace("{{engineer}}", "")
                .replace("{{commenterName}}", "")
                .replace("{{companyName}}", "");
            output += row + "\n";
            template = template.replace(`{{${sentiment}Comments}}`, output);
        } else {
            output = "";
            for (let comment of sortedComments[sentiment]) {
                let engineers = comment["agents"].join(", ");
                let row = rowTemplate
                    .replace("{{comment}}", comment["comment"])
                    .replace("{{engineer}}", engineers)
                    .replace("{{commenterName}}", comment["name"])
                    .replace("{{companyName}}", comment["company"]);
                output += row + "\n";
            }
            template = template.replace(`{{${sentiment}Comments}}`, output);
        }
    }
    return template;
}

/**
 * fills out the weekly email template with the data from the reviews
 * @param {String} template 
 * @param {Object} reviews 
 * @returns {String} template
 */
function createWeeklyEmail(template, reviews) {
    template = _replaceCsatScores(template, reviews, "Weekly");
    template = _replaceWeeklyFeedback(template, reviews);
    template = _replaceLancomRatings(template, reviews, "Weekly");
    template = _replaceDate(template);
    return template;
}
/**
 * Creates the monthly email from a template
 * @param {String} template 
 * @param {Object} monthlyReviews - JSON object 
 * @returns {String} template
 */
function createMonthlyEmail(template, monthlyReviews) {
    template = _replaceDate(template);
    template = _replaceCsatScores(template, monthlyReviews, "Monthly");
    template = _replaceTopThreeAgents(template, monthlyReviews);
    template = _replaceCsatScores(template, monthlyReviews, "Monthly");
    template = _replaceLancomRatings(template, monthlyReviews, "Monthly");
    template = _replaceCompanies(template, monthlyReviews);
    template = _replaceMonthlyComments(template, monthlyReviews);
    template = _replaceTopThreeReviewers(template, monthlyReviews);
    template = _replaceMonthlyComments(template, monthlyReviews);
    return template;
}

export { createWeeklyEmail, createMonthlyEmail };

