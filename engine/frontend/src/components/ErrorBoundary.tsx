import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    // Here you would also log the error to an error reporting service like Sentry
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Ups, algo salió mal</h1>
            <p className="text-slate-600 mb-6">
              Ocurrió un error inesperado. Nuestro equipo ha sido notificado y lo está revisando.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-slate-900 text-white font-semibold py-3 rounded-xl hover:bg-slate-800 transition-colors"
            >
              Volver a cargar la página
            </button>
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-6 p-4 bg-red-50 rounded-lg text-left overflow-auto text-xs font-mono text-red-800">
                {this.state.error?.toString()}
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
