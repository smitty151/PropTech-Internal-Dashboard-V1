import React from "react";

/**
 * Root-level React Error Boundary.
 *
 * Wraps the entire app so an uncaught render/API error renders a graceful
 * fallback panel instead of a white screen. The fallback offers a hard
 * reload and shows the error message in dev/preview environments.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // Keep this minimal — we don't want the boundary itself to throw.
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary]", error, info?.componentStack);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  handleHome = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const message = this.state.error?.message || "An unexpected error occurred.";

    return (
      <div
        data-testid="error-boundary-fallback"
        style={{
          minHeight: "100vh",
          background: "#F7F7F4",
          color: "#0A0A0A",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
          padding: "32px",
        }}
      >
        <div
          style={{
            maxWidth: 520,
            background: "#fff",
            border: "1px solid #E5E5E0",
            padding: "40px 36px",
          }}
        >
          <div
            style={{
              fontSize: 11,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "#9CA3AF",
              marginBottom: 12,
            }}
          >
            PlaceHolder
          </div>
          <h1
            style={{
              fontSize: 28,
              lineHeight: 1.15,
              margin: "0 0 12px",
              fontWeight: 600,
            }}
          >
            Something went wrong.
          </h1>
          <p
            style={{
              color: "#4B5563",
              fontSize: 14,
              lineHeight: 1.6,
              margin: "0 0 20px",
            }}
          >
            We hit an unexpected error while rendering this view. Your session
            is intact — try reloading the page or returning to the home screen.
          </p>
          <pre
            data-testid="error-boundary-message"
            style={{
              background: "#F5F5EE",
              color: "#0A0A0A",
              fontSize: 12,
              lineHeight: 1.5,
              padding: "12px 14px",
              border: "1px solid #E5E5E0",
              overflowX: "auto",
              whiteSpace: "pre-wrap",
              marginBottom: 24,
              fontFamily:
                "ui-monospace, SFMono-Regular, 'SF Mono', monospace",
            }}
          >
            {message}
          </pre>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              data-testid="error-boundary-reload"
              onClick={this.handleReload}
              style={{
                background: "#0A0A0A",
                color: "#fff",
                border: "none",
                padding: "12px 22px",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              Reload page
            </button>
            <button
              data-testid="error-boundary-home"
              onClick={this.handleHome}
              style={{
                background: "#fff",
                color: "#0A0A0A",
                border: "1px solid #0A0A0A",
                padding: "12px 22px",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              Go home
            </button>
          </div>
        </div>
      </div>
    );
  }
}
