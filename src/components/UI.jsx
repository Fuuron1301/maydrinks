/* eslint-disable react-refresh/only-export-components -- shared React hook and components */
import { useEffect, useId, useState } from "react";
import { api, labels } from "../services/api";

export function ErrorBox({ error }) {
  if (!error) return null;
  return (
    <div className="alert" role="alert">
      {typeof error === "string" ? error : error.message}
      {Array.isArray(error.details) && (
        <ul>
          {error.details.map((row, index) => (
            <li key={row.id || index}>
              {row.name}: cần {row.required} {row.unit}, còn {row.available}{" "}
              {row.unit}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
export function Busy() {
  return (
    <div className="loading" role="status">
      Đang tải dữ liệu từ máy chủ…
    </div>
  );
}
export function Title({ title, sub, children }) {
  return (
    <div className="page-heading row">
      <div>
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {children}
    </div>
  );
}
export function Field({ label, as, children, ...props }) {
  const generated = useId();
  const id = props.id || generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {as === "select" ? (
        <select {...props} id={id}>
          {children}
        </select>
      ) : as === "textarea" ? (
        <textarea {...props} id={id} />
      ) : (
        <input {...props} id={id} />
      )}
    </div>
  );
}
export function Status({ value }) {
  return (
    <span className={"status " + (value || "")}>
      {labels[value] || value || "—"}
    </span>
  );
}
export function Data({ path, children, refresh = 0 }) {
  const [state, setState] = useState({
    data: null,
    error: null,
    loading: true,
  });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    api(path)
      .then((data) => {
        if (active) setState({ data, error: null, loading: false });
      })
      .catch((error) => {
        if (active) setState({ data: null, error, loading: false });
      });
    return () => {
      active = false;
    };
  }, [path, refresh, revision]);
  if (state.loading && !state.data) return <Busy />;
  if (state.error)
    return (
      <>
        <ErrorBox error={state.error} />
        <button
          type="button"
          className="btn secondary"
          onClick={() => {
            setState({ data: null, error: null, loading: true });
            setRevision((x) => x + 1);
          }}
        >
          Thử lại
        </button>
      </>
    );
  return state.data ? (
    children(state.data, () => {
      setState((s) => ({ ...s, loading: true }));
      setRevision((x) => x + 1);
    })
  ) : (
    <Busy />
  );
}
export function useAction(notify, reload) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  async function run(path, method, body, headers) {
    setBusy(true);
    setError(null);
    try {
      const value = await api(path, { method, body, headers });
      notify?.("Đã cập nhật thành công.");
      reload?.();
      return value;
    } catch (caught) {
      setError(caught);
      return null;
    } finally {
      setBusy(false);
    }
  }
  return { run, busy, error, setError };
}
export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}
