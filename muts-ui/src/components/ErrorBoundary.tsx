import React, { Component, ReactNode } from 'react';

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 text-red-800">
          <h1 className="text-xl font-bold">UI Error</h1>
          <p>{this.state.error?.toString()}</p>
          <button 
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
            onClick={() => window.location.reload()}>
            Reload UI
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
