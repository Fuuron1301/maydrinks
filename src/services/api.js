const configured = import.meta.env.VITE_API_URL?.replace(/\/+$/, "") || "";
// Development uses Vite's reverse proxy; production requires a public HTTPS API.
export const apiBase = configured || (import.meta.env.DEV ? "/api" : "");
let token = sessionStorage.getItem("may-auth-token") || "";
export const hasToken = () => Boolean(token);
export function setToken(value) {
  token = value || "";
  if (token) sessionStorage.setItem("may-auth-token", token);
  else sessionStorage.removeItem("may-auth-token");
}
export function getApiBase() {
  return apiBase;
}
export async function api(
  path,
  { body, headers = {}, timeoutMs = 90000, ...options } = {},
) {
  if (!apiBase)
    throw new Error(
      "Chưa cấu hình máy chủ API công khai. Quản trị viên cần triển khai backend và đặt VITE_API_URL trước khi xuất bản.",
    );
  const controller = new AbortController();
  const requestToken = token;
  const cancel = () => controller.abort(options.signal?.reason);
  if (options.signal?.aborted) cancel();
  else options.signal?.addEventListener("abort", cancel, { once: true });
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(apiBase + path, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(requestToken ? { Authorization: "Bearer " + requestToken } : {}),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const type = response.headers.get("content-type") || "";
    if (!type.includes("application/json"))
      throw new Error("Máy chủ API chưa được cấu hình đúng (không trả JSON).");
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.error || "Yêu cầu thất bại.");
      error.status = response.status;
      error.details = data.details;
      if (
        response.status === 401 &&
        path !== "/auth/login" &&
        token === requestToken
      ) {
        setToken("");
        window.dispatchEvent(new Event("may-auth-expired"));
      }
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error("Máy chủ phản hồi chậm. Vui lòng thử lại.", {
        cause: error,
      });
    if (error instanceof TypeError)
      throw new Error(
        "Không kết nối được máy chủ API. Kiểm tra kết nối hoặc cấu hình backend.",
        { cause: error },
      );
    throw error;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", cancel);
  }
}
export const money = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(
    value || 0,
  );
export const dateTime = (value) =>
  value
    ? new Date(value).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })
    : "—";
export const labels = {
  pending: "Chờ xác nhận",
  preparing: "Đang pha chế",
  ready: "Sẵn sàng",
  completed: "Hoàn tất",
  cancelled: "Đã hủy",
};
export const choiceText = (c) =>
  [
    c?.size?.name,
    c?.sugar?.name,
    c?.ice?.name,
    ...(c?.toppings || []).map((x) => x.name),
  ]
    .filter(Boolean)
    .join(" · ");
