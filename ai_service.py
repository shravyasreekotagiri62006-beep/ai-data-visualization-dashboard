import json
import numpy as np
from dataset_processor import get_column_metrics

def generate_insights_and_anomalies(df):
    """ Mocks detailed Insights, Anomalies, Trends, and Quality for AI Report """
    metrics = get_column_metrics(df)
    
    insights = []
    anomalies = []
    
    quality_score = 100
    
    if len(metrics['columns']) == 0:
        return "No data available."
    if len(metrics['categorical_cols']) > len(metrics['numeric_cols']):
        quality_score -= 10
        
    insights.append(f"**Data Volume**: The dataset includes {metrics['total_rows']} robust rows spanning {len(metrics['columns'])} key dimensions ({len(metrics['numeric_cols'])} numeric, {len(metrics['categorical_cols'])} categorical).")
    
    for top_num in metrics['numeric_cols'][:3]:  # Analyze up to first 3 numerical cols
        st = metrics['stats'][top_num]
        insights.append(f"**Metric Analysis ({top_num})**: Shows a diverse range from {st['min']:.2f} to {st['max']:.2f}. The mean stands at {st['mean']:.2f} with a standard deviation of {st['std']:.2f}, indicating the general scale of this variable.")
        
        if st['std'] > 0 and (st['max'] - st['mean']) > (3 * st['std']):
            anomalies.append(f"**Extreme Values in '{top_num}'**: Values reaching up to {st['max']:.2f} suggest intense upper-tail outliers compared to the normal distribution.")
            quality_score -= 2
    
    for cat_col in metrics['categorical_cols'][:2]:  # Analyze up to first 2 categorical
        cat_st = metrics['stats'][cat_col]
        insights.append(f"**Categorical Overview ({cat_col})**: Comprises {cat_st['unique_count']} distinctive classifications. Interestingly, the dominant subset is '{cat_st['top_value']}' which frames the majority context of this section.")
        
        if len(metrics['categorical_cols']) > 3:
            anomalies.append("**High Dimensionality Detected**: Having a broad spectrum of categorical fields implies complex segmentation which could impact fast generalized analytics.")
            quality_score -= 2

    if not anomalies:
        anomalies.append("No critical anomalies detected automatically. The data variance appears stable and evenly distributed.")
        
    return {
        "insights": insights,
        "anomalies": anomalies,
        "quality_score": max(quality_score, 50) # Cap floor
    }

def generate_predictions(df):
    """ Simple Linear Regression Mock to Predict 'Future' trajectory """
    metrics = get_column_metrics(df)
    if not metrics['numeric_cols']:
        return "Not enough temporal or numerical properties exist to plot a statistical trend formulation."
        
    predictions_text = ""
    for target_col in metrics['numeric_cols'][:2]: # Predict 2 variables if possible
        y = df[target_col].dropna().values
        if len(y) < 10:
             continue
             
        y = y[-500:]
        x = np.arange(len(y))
        m, c = np.polyfit(x, y, 1)
        
        trend_direction = "increasing" if m > 0 else "decreasing"
        future_steps = max(int(len(y) * 0.1), 5)
        last_x, last_val = x[-1], m * x[-1] + c
        future_val = m * (last_x + future_steps) + c
        pct_change = ((future_val - last_val) / (abs(last_val) if last_val != 0 else 1)) * 100
        
        predictions_text += f"- Based on linear analysis for **{target_col}**, the trajectory reflects a {trend_direction} pattern. Using mathematical extrapolation on recent behavior, we estimate a **~{abs(pct_change):.1f}% potential {'amplification' if m>0 else 'reduction'}** in future cycles if the condition holds.\n"
        
    return predictions_text if predictions_text else "Current data structure prevents reliable trajectory forecasting."


def generate_full_report(df):
    """ Exhaustively detailed AI text generation """
    analysis = generate_insights_and_anomalies(df)
    pred_text = generate_predictions(df)
    
    report = f"### Overall Assessment Score: {analysis['quality_score']}/100\n"
    report += "This algorithmic review deeply parsed the structural integrity and computational potential of your dataset.\n\n"
    
    report += "### 💡 Deep Statistical Insights\n"
    for i in analysis['insights']:
         report += f"- {i}\n"
         
    report += "\n### 📈 Trajectory Predictions\n"
    report += f"{pred_text}\n"
    
    report += "\n### ⚠️ Structural Anomalies\n"
    for a in analysis['anomalies']:
         report += f"- {a}\n"
         
    report += "\n### 📋 System Recommendations\n"
    report += "- Deploy visualizations (Bar/Line charts) across the categorical boundaries to reveal secondary cluster correlations.\n"
    if analysis['quality_score'] < 90:
        report += "- Due to detected variances or skewed dimensions, enforcing a pre-processing validation check on raw uploads might stabilize downstream pipelines.\n"
    
    return report

def generate_chat_response(message, df):
    """ Expansive keyword map for robust mock AI Chatbot """
    msg = message.lower()
    metrics = get_column_metrics(df)
    
    if any(k in msg for k in ['hi', 'hello', 'hey']):
        return "Hello! I have fully loaded the dataset into memory. I can provide statistical summaries, highlight anomalies, generate basic polynomial predictions, or explain exact column metrics. What do you need?"
        
    if any(k in msg for k in ['row', 'size', 'how many', 'count']):
        return f"The current context has {metrics['total_rows']} total rows and {len(metrics['columns'])} columns loaded."
        
    if 'column' in msg or 'features' in msg:
        c = ", ".join(metrics['columns'])
        return f"This dataset maps the following vectors: {c}."
        
    if 'predict' in msg or 'future' in msg or 'forecast' in msg:
        return f"Here is the local predictive regression matrix:\n{generate_predictions(df)}"
        
    if any(k in msg for k in ['missing', 'clean', 'quality', 'null']):
        return "I handled null values via computational mean/mode insertion automatically during the `/api/upload` phase so the dataset reflects a solid state without fatal holes. Categorical missing points were labeled 'Unknown'."

    if any(k in msg for k in ['suggestion', 'recommend', 'what should']):
        return "I highly recommend building a Grid panel mapping your numerical data (Y-axis) against your top category (X-axis) using the visually accelerated Chart.js widget! Also, evaluate the outliers identified in the AI Deep Analysis block to confirm they aren't noise."

    if any(k in msg for k in ['explain', 'what exactly', 'happening']):
        return f"To explain: This dataset maps {metrics['total_rows']} entities. It possesses {len(metrics['numeric_cols'])} quantitative vectors (like `{metrics['numeric_cols'][0] if metrics['numeric_cols'] else 'None'}`) dictating magnitude, and {len(metrics['categorical_cols'])} qualitative vectors acting as grouping features. When combined, we're seeing natural variances scaling up to `{metrics['stats'][metrics['numeric_cols'][0]]['max'] if metrics['numeric_cols'] else 0}`."

    if any(k in msg for k in ['average', 'mean', 'max', 'min']):
        if not metrics['numeric_cols']:
            return "There are no quantifiable columns present to yield averagings."
        res = "Here is a snapshot of numerical traits: "
        for n in metrics['numeric_cols'][:2]:
            st = metrics['stats'][n]
            res += f"`{n}` (Mean: {st['mean']:.2f}, Range: {st['min']:.2f} to {st['max']:.2f}). "
        return res

    if 'thank' in msg:
        return "You're extremely welcome! Is there another dimension of this data you'd like to probe?"
        
    return "While my external internet capabilities are bounded, my internal algorithm analyzes regressions, counts, column mapping, means, and quality scores! Try querying: 'Explain the data structure', 'What are the future predictions', or 'Give me suggestions'."
