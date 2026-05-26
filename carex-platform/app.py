# app.py - CARE-X Modified for Clinical Trial (Phase 2/3 Integration)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

st.set_page_config(
    page_title="CARE-X | Escalation Support Framework",
    page_icon="⚕️",
    layout="wide"
)

# ============================================================================
# CLINICAL VALIDATION GUARDRAILS
# ============================================================================

class ClinicalInputValidator:
    """Safety guardrails with baseline-adjusted relative hypotension detection"""
    
    VALIDATION_RANGES = {
        'sbp': {'min': 40, 'max': 250, 'unit': 'mmHg'},
        'hr': {'min': 20, 'max': 250, 'unit': 'bpm'},
        'rr': {'min': 5, 'max': 60, 'unit': '/min'},
        'spo2': {'min': 50, 'max': 100, 'unit': '%'},
        'temperature': {'min': 30, 'max': 43, 'unit': '°C'},
        'lactate': {'min': 0, 'max': 25, 'unit': 'mmol/L'},
        'troponin': {'min': 0, 'max': 50000, 'unit': 'ng/L'},
        'creatinine': {'min': 20, 'max': 1500, 'unit': 'µmol/L'}
    }
    
    @classmethod
    def validate_value(cls, parameter: str, value: float) -> Tuple[bool, str]:
        if parameter not in cls.VALIDATION_RANGES:
            return True, ""
        
        ranges = cls.VALIDATION_RANGES[parameter]
        
        if value < ranges['min']:
            return False, f"{parameter.upper()} {value} {ranges['unit']} is below plausible range (min: {ranges['min']})"
        if value > ranges['max']:
            return False, f"{parameter.upper()} {value} {ranges['unit']} exceeds plausible range (max: {ranges['max']})"
        
        return True, ""


# ============================================================================
# PHASE 2: GRAY AREA DETECTION ENGINES (Modified for Proposal)
# ============================================================================

class RelativeHypotensionDetector:
    """Detects relative hypotension based on patient baseline"""
    
    @staticmethod
    def assess(current_sbp: float, baseline_sbp: float, hr: float, troponin_trend: str = 'stable') -> Dict:
        """Critical for the Deceptive Compensator case"""
        sbp_drop = baseline_sbp - current_sbp
        percent_drop = (sbp_drop / baseline_sbp) * 100
        
        if baseline_sbp > 130 and current_sbp > 90:
            # Hypertensive patient with "normal" BP but significant drop
            if percent_drop > 20:
                return {
                    'relative_hypotension': True,
                    'severity': 'HIGH',
                    'message': f"⚠️ RELATIVE HYPOTENSION: SBP dropped {sbp_drop:.0f} mmHg ({percent_drop:.0f}%) from baseline of {baseline_sbp:.0f}. Despite SBP > 90, this represents significant cardiovascular strain for a hypertensive patient.",
                    'recommendation': 'Immediate ICU evaluation warranted despite "normal" absolute values'
                }
            elif percent_drop > 15:
                return {
                    'relative_hypotension': True,
                    'severity': 'MODERATE',
                    'message': f"Relative hypotension detected: SBP dropped {sbp_drop:.0f} mmHg from baseline {baseline_sbp:.0f}. Monitor closely.",
                    'recommendation': 'Consider early senior review'
                }
        
        # Troponin + hypotension interaction
        if troponin_trend == 'rising' and current_sbp < 110:
            return {
                'relative_hypotension': True,
                'severity': 'CRITICAL',
                'message': f"CRITICAL: Rising troponin with SBP {current_sbp} suggests myocardial injury with inadequate perfusion pressure.",
                'recommendation': 'Immediate cardiology/ICU consultation'
            }
        
        return {'relative_hypotension': False, 'severity': 'LOW', 'message': 'No relative hypotension detected'}


class TransientCompensationDetector:
    """Detects false reassurance after fluid bolus - The Transient Fluid Responder case"""
    
    @staticmethod
    def assess(hr_trend: List[float], sbp_trend: List[float], troponin_trend: List[float], 
               fluid_given: bool = False) -> Dict:
        
        if not fluid_given or len(hr_trend) < 3:
            return {'transient_compensation': False}
        
        hr_rebound = False
        sbp_improvement = sbp_trend[-1] > sbp_trend[-2] if len(sbp_trend) >= 2 else False
        hr_persistent = hr_trend[-1] > 105 if hr_trend else False
        troponin_rising = troponin_trend[-1] > troponin_trend[-2] if len(troponin_trend) >= 2 else False
        
        # Key pattern: BP improves but HR remains high + troponin rising
        if sbp_improvement and hr_persistent and troponin_rising:
            return {
                'transient_compensation': True,
                'severity': 'HIGH',
                'message': "⚠️ FALSE REASSURANCE DETECTED: Blood pressure improved after fluids, but persistent tachycardia (breaking through) and rising troponin indicate compensation is failing. Underlying myocardial injury is progressing.",
                'recommendation': "Do NOT be reassured by BP response. Immediate escalation for suspected acute coronary syndrome."
            }
        
        if sbp_improvement and hr_persistent:
            return {
                'transient_compensation': True,
                'severity': 'MODERATE',
                'message': "Transient BP response with persistent breakthrough tachycardia suggests compensation may be inadequate.",
                'recommendation': "Consider early ICU liaison review"
            }
        
        return {'transient_compensation': False}


class TroponinDynamicsEngine:
    """Primary driver for gray area detection - Silent Myocardial Injury case"""
    
    @staticmethod
    def analyze(troponin_values: List[float], timestamps: List[datetime]) -> Dict:
        if len(troponin_values) < 2:
            return {'trend': 'stable', 'message': 'Insufficient troponin data'}
        
        initial = troponin_values[0]
        latest = troponin_values[-1]
        delta = latest - initial
        percent_change = (delta / initial) * 100 if initial > 0 else 0
        
        # Dynamic pattern recognition
        if delta > 100 and percent_change > 100:
            return {
                'trend': 'explosive_rise',
                'delta': delta,
                'percent_change': percent_change,
                'message': f"⚠️ EXPLOSIVE TROPONIN RISE: {initial:.0f} → {latest:.0f} ng/L ({percent_change:.0f}% increase). Strongly suggests acute myocardial injury.",
                'recommendation': 'Immediate cardiology consultation, prepare for cath lab'
            }
        elif delta > 50 and percent_change > 50:
            return {
                'trend': 'significant_rise',
                'delta': delta,
                'percent_change': percent_change,
                'message': f"Significant troponin rise: {initial:.0f} → {latest:.0f} ng/L. Indicates evolving myocardial injury.",
                'recommendation': 'Urgent cardiology review'
            }
        elif delta > 20:
            return {
                'trend': 'rising',
                'delta': delta,
                'percent_change': percent_change,
                'message': f"Troponin rising: {initial:.0f} → {latest:.0f} ng/L. Monitor for ongoing injury.",
                'recommendation': 'Repeat troponin in 1-2 hours'
            }
        
        return {'trend': 'stable', 'message': 'Troponin stable', 'recommendation': 'Continue monitoring'}


class EscalationUncertaintyModel:
    """Updated for gray area traps from proposal"""
    
    @staticmethod
    def assess(physiological_history: List[Dict], baseline_sbp: float, 
               troponin_analysis: Dict, fluid_given: bool = False) -> Dict:
        
        if not physiological_history:
            return {'level': 'LOW', 'confidence': 85, 'gray_area_traps': []}
        
        latest = physiological_history[-1]
        gray_area_traps = []
        score = 0
        
        # TRAP 1: Relative Hypotension (Deceptive Compensator)
        rel_hypo = RelativeHypotensionDetector.assess(
            latest.get('sbp', 120), baseline_sbp, 
            latest.get('hr', 80), troponin_analysis.get('trend', 'stable')
        )
        if rel_hypo.get('relative_hypotension'):
            gray_area_traps.append({
                'name': 'Deceptive Compensator (Relative Hypotension)',
                'severity': rel_hypo['severity'],
                'message': rel_hypo['message']
            })
            score += 3 if rel_hypo['severity'] in ['HIGH', 'CRITICAL'] else 2
        
        # TRAP 2: Transient Fluid Response (False Reassurance)
        if fluid_given:
            hr_trend = [obs.get('hr', 80) for obs in physiological_history[-3:]]
            sbp_trend = [obs.get('sbp', 120) for obs in physiological_history[-3:]]
            trop_trend = [obs.get('troponin', 10) for obs in physiological_history[-3:] if obs.get('troponin')]
            
            transient = TransientCompensationDetector.assess(hr_trend, sbp_trend, trop_trend, fluid_given)
            if transient.get('transient_compensation'):
                gray_area_traps.append({
                    'name': 'False Reassurance (Transient Fluid Responder)',
                    'severity': transient['severity'],
                    'message': transient['message']
                })
                score += 3
        
        # TRAP 3: Silent Myocardial Injury
        if troponin_analysis.get('trend') in ['explosive_rise', 'significant_rise']:
            if latest.get('sbp', 120) > 100:  # Normotensive but troponin surging
                gray_area_traps.append({
                    'name': 'Silent Myocardial Injury',
                    'severity': 'HIGH',
                    'message': f"Normotensive ({latest.get('sbp', 120)} mmHg) but troponin {troponin_analysis.get('trend')}. Do NOT dismiss tachycardia as anxiety.",
                    'recommendation': troponin_analysis.get('recommendation')
                })
                score += 3
        
        # Escalation confidence (inverse of gray area complexity)
        if score <= 2:
            level = 'LOW'
            confidence = 85
            message = "No active gray area traps detected. Standard monitoring appropriate."
        elif score <= 5:
            level = 'MODERATE'
            confidence = 60
            message = "Gray area ambiguity detected. Escalation consideration is reasonable despite incomplete overt criteria."
        elif score <= 8:
            level = 'HIGH'
            confidence = 35
            message = "Multiple gray area traps identified. Strongly consider escalation before overt decompensation."
        else:
            level = 'CRITICAL'
            confidence = 15
            message = "Critical gray area pattern: Immediate escalation recommended."
        
        return {
            'level': level,
            'confidence': confidence,
            'message': message,
            'gray_area_traps': gray_area_traps,
            'score': score
        }


class EscalationRationaleEngine:
    """Explains WHY escalation despite incomplete criteria - Proposal-aligned"""
    
    @staticmethod
    def generate(uncertainty: Dict, rel_hypo: Dict, transient: Dict, 
                 troponin: Dict, baseline_sbp: float) -> List[str]:
        
        rationale = []
        
        # Relative hypotension rationale
        if rel_hypo.get('relative_hypotension'):
            rationale.append(
                f"Current SBP {rel_hypo.get('current_sbp', '?')} mmHg represents a significant drop from baseline {baseline_sbp} mmHg. "
                "Standard early warning scores may miss this relative hypotension, but it indicates significant cardiovascular strain."
            )
        
        # Transient compensation rationale
        if transient.get('transient_compensation'):
            rationale.append(
                "The transient blood pressure response to fluids may create false reassurance. "
                "Persistent breakthrough tachycardia suggests compensation is failing, and rising troponin indicates ongoing injury."
            )
        
        # Troponin rationale
        if troponin.get('trend') in ['explosive_rise', 'significant_rise']:
            rationale.append(
                f"The dynamic troponin pattern ({troponin.get('message', '')}) is the key differentiator here. "
                "Normotension does NOT exclude acute myocardial injury requiring immediate intervention."
            )
        
        # General gray area rationale
        if uncertainty['level'] in ['HIGH', 'MODERATE']:
            rationale.append(
                "Delayed escalation until overt shock criteria develop risks sudden decompensation. "
                "Early ICU review in the 'gray area' is associated with better outcomes."
            )
        
        return rationale if rationale else ["No active escalation concerns. Continue standard monitoring."]


# ============================================================================
# DECISION CONCORDANCE TRACKING (For Clinical Trial)
# ============================================================================

class DecisionConcordanceTracker:
    """Tracks physician decisions against Delphi-established ground truth"""
    
    @staticmethod
    def calculate_concordance(physician_action: str, ground_truth_action: str) -> Dict:
        action_mapping = {
            'maintain': ['Continue monitoring', 'Observation', 'Routine care'],
            'senior_review': ['Senior review', 'Physician review', 'Urgent review'],
            'icu_consult': ['ICU consultation', 'ICU liaison', 'Critical care review'],
            'icu_transfer': ['ICU transfer', 'Immediate ICU', 'Critical care activation'],
            'cath_lab': ['Cath lab', 'Cardiology intervention', 'PCI']
        }
        
        physician_category = None
        for cat, actions in action_mapping.items():
            if any(action.lower() in physician_action.lower() for action in actions):
                physician_category = cat
                break
        
        concordant = (physician_category == ground_truth_action)
        
        return {
            'concordant': concordant,
            'physician_category': physician_category,
            'ground_truth': ground_truth_action,
            'concordance_score': 100 if concordant else 0
        }


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def initialize_session_state():
    """Initialize with Deceptive Compensator case (hypertensive patient)"""
    if 'physiological_history' not in st.session_state:
        start_time = datetime.now() - timedelta(hours=6)
        st.session_state.physiological_history = [
            {'time': start_time + timedelta(hours=0), 'sbp': 148, 'hr': 88, 'troponin': 12, 'lactate': 1.2, 'rr': 16, 'spo2': 97},
            {'time': start_time + timedelta(hours=2), 'sbp': 135, 'hr': 95, 'troponin': 28, 'lactate': 1.5, 'rr': 18, 'spo2': 96},
            {'time': start_time + timedelta(hours=4), 'sbp': 118, 'hr': 104, 'troponin': 65, 'lactate': 1.9, 'rr': 20, 'spo2': 95},
            {'time': start_time + timedelta(hours=6), 'sbp': 108, 'hr': 112, 'troponin': 120, 'lactate': 2.4, 'rr': 22, 'spo2': 94}
        ]
    
    if 'baseline_sbp' not in st.session_state:
        st.session_state.baseline_sbp = 150  # Hypertensive baseline
    
    if 'fluid_given' not in st.session_state:
        st.session_state.fluid_given = False
    
    if 'clinical_decisions' not in st.session_state:
        st.session_state.clinical_decisions = []
    
    if 'case_type' not in st.session_state:
        st.session_state.case_type = "Deceptive Compensator (Hypertensive Baseline)"


def add_observation(sbp, hr, troponin, lactate, rr, spo2):
    new_obs = {
        'time': datetime.now(),
        'sbp': sbp,
        'hr': hr,
        'troponin': troponin,
        'lactate': lactate,
        'rr': rr,
        'spo2': spo2
    }
    st.session_state.physiological_history.append(new_obs)
    
    if len(st.session_state.physiological_history) > 20:
        st.session_state.physiological_history = st.session_state.physiological_history[-20:]


def main():
    initialize_session_state()
    
    # Header
    st.title("⚕️ CARE-X | Escalation Support Framework")
    st.caption("Navigating the Clinical Gray Area | ICEM 2026 Hamburg")
    st.markdown("---")
    
    current = st.session_state.physiological_history[-1]
    
    # Sidebar - Clinical Input
    with st.sidebar:
        st.header("📋 Patient Context")
        
        st.info(f"**Case Type:** {st.session_state.case_type}")
        st.metric("Baseline SBP", f"{st.session_state.baseline_sbp} mmHg", 
                  help="Patient's known baseline blood pressure")
        
        st.markdown("---")
        st.header("📝 New Observation")
        
        col1, col2 = st.columns(2)
        with col1:
            new_sbp = st.number_input("SBP (mmHg)", min_value=40, max_value=250, 
                                     value=int(current['sbp']), step=1)
            new_hr = st.number_input("Heart Rate (bpm)", min_value=20, max_value=250, 
                                    value=int(current['hr']), step=1)
        with col2:
            new_troponin = st.number_input("Troponin (ng/L)", min_value=0, max_value=50000, 
                                          value=int(current['troponin']), step=10)
            new_lactate = st.number_input("Lactate (mmol/L)", min_value=0.0, max_value=25.0, 
                                         value=float(current['lactate']), step=0.1)
        
        new_rr = st.number_input("Respiratory Rate (/min)", min_value=5, max_value=60, 
                                value=int(current['rr']), step=1)
        new_spo2 = st.number_input("SpO₂ (%)", min_value=50, max_value=100, 
                                  value=int(current['spo2']), step=1)
        
        st.markdown("---")
        st.markdown("### Interventions Given")
        fluid_bolus = st.checkbox("IV Fluid Bolus Given", value=st.session_state.fluid_given)
        
        if fluid_bolus != st.session_state.fluid_given:
            st.session_state.fluid_given = fluid_bolus
        
        if st.button("➕ Add Observation", type="primary"):
            add_observation(new_sbp, new_hr, new_troponin, new_lactate, new_rr, new_spo2)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎯 Your Escalation Decision")
        
        decision = st.radio(
            "Select your management plan:",
            ['Continue monitoring', 'Senior physician review', 'ICU consultation', 'Immediate ICU transfer', 'Cardiology/cath lab activation']
        )
        
        if st.button("✅ Submit Decision", type="secondary"):
            st.session_state.clinical_decisions.append({
                'time': datetime.now(),
                'decision': decision,
                'case_type': st.session_state.case_type,
                'vitals': f"SBP {current['sbp']}, HR {current['hr']}, Troponin {current['troponin']}"
            })
            st.success(f"Decision recorded: {decision}")
    
    # MAIN DISPLAY AREA
    current = st.session_state.physiological_history[-1]
    
    # Extract troponin trend
    troponin_values = [obs['troponin'] for obs in st.session_state.physiological_history if 'troponin' in obs]
    troponin_times = [obs['time'] for obs in st.session_state.physiological_history if 'troponin' in obs]
    
    troponin_analysis = TroponinDynamicsEngine.analyze(troponin_values, troponin_times)
    rel_hypo = RelativeHypotensionDetector.assess(
        current['sbp'], st.session_state.baseline_sbp, 
        current['hr'], troponin_analysis.get('trend', 'stable')
    )
    
    hr_trend = [obs['hr'] for obs in st.session_state.physiological_history[-3:]]
    sbp_trend = [obs['sbp'] for obs in st.session_state.physiological_history[-3:]]
    trop_trend = [obs['troponin'] for obs in st.session_state.physiological_history[-3:] if 'troponin' in obs]
    
    transient = TransientCompensationDetector.assess(
        hr_trend, sbp_trend, trop_trend, st.session_state.fluid_given
    )
    
    uncertainty = EscalationUncertaintyModel.assess(
        st.session_state.physiological_history, 
        st.session_state.baseline_sbp,
        troponin_analysis,
        st.session_state.fluid_given
    )
    
    rationale = EscalationRationaleEngine.generate(
        uncertainty, rel_hypo, transient, troponin_analysis, st.session_state.baseline_sbp
    )
    
    # Dashboard
    st.subheader("📊 Current Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("SBP", f"{current['sbp']} mmHg", 
                 f"{current['sbp'] - st.session_state.baseline_sbp:+.0f} from baseline")
    with col2:
        st.metric("Heart Rate", f"{current['hr']} bpm")
    with col3:
        st.metric("Troponin", f"{current['troponin']} ng/L",
                 f"{current['troponin'] - troponin_values[-2] if len(troponin_values) > 1 else 0:+.0f}")
    with col4:
        st.metric("Lactate", f"{current['lactate']} mmol/L")
    with col5:
        st.metric("Gray Area Score", f"{uncertainty['score']}/12",
                 help="Higher score = more gray area complexity")
    
    # GRAY AREA TRAPS (Primary Display)
    st.markdown("---")
    st.subheader("🎯 Clinical Gray Area Assessment")
    
    if uncertainty['gray_area_traps']:
        for trap in uncertainty['gray_area_traps']:
            severity_color = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MODERATE': '🟡',
                'LOW': '🟢'
            }.get(trap['severity'], '⚪')
            
            st.markdown(f"""
            <div style="background-color: {'#f8d7da' if trap['severity'] in ['HIGH', 'CRITICAL'] else '#fff3cd'}; 
                        padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; 
                        border-left: 4px solid {'#dc3545' if trap['severity'] in ['HIGH', 'CRITICAL'] else '#ffc107'}">
                <strong>{severity_color} {trap['name']}</strong><br>
                {trap['message']}<br>
                <em>Recommendation: {trap.get('recommendation', 'Escalation consideration warranted')}</em>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active gray area traps detected. Standard monitoring appropriate.")
    
    # Relative Hypotension Highlight
    if rel_hypo.get('relative_hypotension'):
        st.warning(rel_hypo['message'])
    
    # Transient Compensation Warning
    if transient.get('transient_compensation'):
        st.error(transient['message'])
    
    # Escalation Uncertainty Level
    st.markdown(f"""
    <div style="background-color: {'#d4edda' if uncertainty['level'] == 'LOW' else '#fff3cd' if uncertainty['level'] == 'MODERATE' else '#f8d7da' if uncertainty['level'] == 'HIGH' else '#d1ecf1'}; 
                padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
        <strong>ESCALATION UNCERTAINTY: {uncertainty['level']}</strong><br>
        {uncertainty['message']}<br>
        <strong>Escalation Confidence: {uncertainty['confidence']}%</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Escalation Rationale
    st.subheader("📋 Why Escalation Deserves Consideration")
    for r in rationale:
        st.markdown(f"- {r}")
    
    # Trend Visualization - Focus on Troponin Dynamics
    st.markdown("---")
    st.subheader("📈 Critical Trends (6-12 Hour Decision Window)")
    
    df_history = pd.DataFrame(st.session_state.physiological_history)
    df_history['time_str'] = df_history['time'].dt.strftime('%H:%M')
    
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=('SBP Trend (with Baseline)', 'Troponin Dynamics (Primary Driver)',
                                       'Heart Rate Trend', 'Lactate Trend'))
    
    # SBP with baseline
    fig.add_trace(go.Scatter(x=df_history['time_str'], y=df_history['sbp'], 
                            mode='lines+markers', name='SBP', line=dict(color='red', width=2)), row=1, col=1)
    fig.add_hline(y=st.session_state.baseline_sbp, line_dash="dash", line_color="gray", row=1, col=1,
                 annotation_text=f"Baseline {st.session_state.baseline_sbp}")
    fig.add_hline(y=90, line_dash="dash", line_color="red", row=1, col=1, annotation_text="Absolute threshold")
    
    # Troponin
    fig.add_trace(go.Scatter(x=df_history['time_str'], y=df_history['troponin'], 
                            mode='lines+markers', name='Troponin', line=dict(color='purple', width=3)), row=1, col=2)
    
    # Heart Rate
    fig.add_trace(go.Scatter(x=df_history['time_str'], y=df_history['hr'], 
                            mode='lines+markers', name='HR', line=dict(color='orange', width=2)), row=2, col=1)
    fig.add_hline(y=100, line_dash="dash", line_color="orange", row=2, col=1, annotation_text="Tachycardia")
    
    # Lactate
    fig.add_trace(go.Scatter(x=df_history['time_str'], y=df_history['lactate'], 
                            mode='lines+markers', name='Lactate', line=dict(color='blue', width=2)), row=2, col=2)
    fig.add_hline(y=2.0, line_dash="dash", line_color="blue", row=2, col=2, annotation_text="Upper normal")
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="Time")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Dynamic Troponin Interpretation
    st.info(f"**Troponin Dynamics:** {troponin_analysis['message']}")
    
    # Decision History (For Trial)
    if st.session_state.clinical_decisions:
        st.markdown("---")
        st.subheader("📋 Your Decision History")
        for d in st.session_state.clinical_decisions[-3:]:
            st.caption(f"{d['time'].strftime('%H:%M')} → {d['decision']}")
    
    # Footer
    st.markdown("---")
    st.caption("⚕️ **CARE-X | Escalation Support Framework**")
    st.caption("Focus: Relative Hypotension • Transient Compensation • Silent Myocardial Injury • Gray Area Decision Support")
    st.caption("ICEM 2026 Hamburg | Hackathon Prototype")


if __name__ == "__main__":
    main()