import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Plane, Map, Building, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import './index.css';

function App() {
  const [query, setQuery] = useState('');
  const [travelerName, setTravelerName] = useState('');
  const [tripStyle, setTripStyle] = useState('Comfort Traveller');
  const [loading, setLoading] = useState(false);
  
  const [currentStep, setCurrentStep] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [result, setResult] = useState(null);

  const handleGenerate = () => {
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setCurrentStep(1);
    setStatusMessage('Connecting to AI Travel Planner...');

    const params = new URLSearchParams({
      query: query,
      traveler_name: travelerName,
      trip_style: tripStyle
    });

    const eventSource = new EventSource(`http://localhost:8000/api/plan/stream?${params.toString()}`);

    eventSource.addEventListener('step', (e) => {
      const data = JSON.parse(e.data);
      setCurrentStep(data.step);
      setStatusMessage(data.message);
    });

    eventSource.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data);
      setResult(data);
      setCurrentStep(4);
      setStatusMessage('');
      setLoading(false);
      eventSource.close();
    });

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      setStatusMessage('An error occurred while generating the plan.');
      setLoading(false);
      eventSource.close();
    };
  };

  return (
    <>
      <div className="hero">
        <h1>Multi Agent <br /><em>Travel Support</em></h1>
        <p>Unlock personalized, luxury travel itineraries customized for your unique style and schedule.</p>
      </div>

      <div className="container">
        <div className="search-card">
          <div className="input-group">
            <label>Where would you like to travel?</label>
            <textarea 
              rows="3" 
              placeholder="e.g. Plan a 5-day trip from Mumbai to Paris in December, budget ₹1.5 lakhs"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          
          <div className="row">
            <div className="input-group">
              <label>Your Name</label>
              <input 
                type="text" 
                placeholder="e.g. Mansi"
                value={travelerName}
                onChange={(e) => setTravelerName(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label>Trip Style</label>
              <select value={tripStyle} onChange={(e) => setTripStyle(e.target.value)}>
                <option>Budget Explorer</option>
                <option>Comfort Traveller</option>
                <option>Luxury Escape</option>
                <option>Adventure Seeker</option>
              </select>
            </div>
          </div>

          <button 
            className="primary" 
            onClick={handleGenerate}
            disabled={loading || !query.trim()}
          >
            {loading ? <><Loader2 className="inline-icon spin" /> Generating Plan...</> : <><Sparkles className="inline-icon" /> Generate My Travel Plan</>}
          </button>
        </div>

        {currentStep > 0 && (
          <div className="progress-tracker">
            {[
              { num: 1, label: 'Flights', icon: Plane },
              { num: 2, label: 'Hotels', icon: Building },
              { num: 3, label: 'Itinerary', icon: Map },
              { num: 4, label: 'Done', icon: CheckCircle2 }
            ].map(step => {
              const Icon = step.icon;
              return (
                <div key={step.num} className={`step ${currentStep === step.num ? 'active' : ''} ${currentStep > step.num ? 'completed' : ''}`}>
                  <div className="step-circle">
                    {currentStep > step.num ? <CheckCircle2 size={16} /> : step.num}
                  </div>
                  <div className="step-label">{step.label}</div>
                </div>
              );
            })}
          </div>
        )}

        {statusMessage && <div className="status-message">{statusMessage}</div>}

        {result && (
          <div className="results-container">
            <div className="result-card">
              <h2><Map className="inline-icon" /> Your Complete Travel Itinerary</h2>
              <div className="markdown-body">
                <ReactMarkdown>{result.itinerary}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="footer">
        <div className="footer-inner">
          <p>Designed & Developed by <strong>Mansi Kumari</strong></p>
          <p>For support and contact: <a href="mailto:mansikumari117@gmail.com">mansikumari117@gmail.com</a></p>
        </div>
      </div>
    </>
  );
}

export default App;
