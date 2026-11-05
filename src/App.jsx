import { useCallback, useEffect, useRef, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { api, apiBase, hasToken, setToken } from "./services/api";
import { Busy, ErrorBox } from "./components/UI";
import {
  Home,
  Menu,
  Detail,
  Cart,
  Checkout,
  Orders,
  OrderDetail,
} from "./pages/Shop";
import { StaffBoard, StaffOrders, StaffOrderDetail } from "./pages/StaffPages";
import { Auth, PasswordPage, Account } from "./pages/Account";
import { Dashboard, Reports, MenuAdmin, Inventory } from "./pages/AdminCore";
import {
  OptionsAdmin,
  Recipes,
  Receipts,
  Users,
  Coupons,
  Audit,
} from "./pages/AdminExtra";

function Guard({ session, roles, children }) {
  if (!session.ready) return <Busy />;
  if (!session.user) return <Navigate to="/login" replace />;
  if (!roles.includes(session.user.role))
    return (
      <Navigate
        to={
          session.user.role === "admin"
            ? "/admin/overview"
            : session.user.role === "staff"
              ? "/staff/board"
              : "/account"
        }
        replace
      />
    );
  return children;
}
const adminLinks = [
  ["/admin/overview", "Tổng quan"],
  ["/admin/menu", "Thực đơn"],
  ["/admin/options", "Tùy chọn"],
  ["/admin/inventory", "Nguyên liệu"],
  ["/admin/recipes", "Công thức"],
  ["/admin/receipts", "Phiếu nhập"],
  ["/admin/orders", "Đơn hàng"],
  ["/admin/reports", "Báo cáo"],
  ["/admin/coupons", "Mã ưu đãi"],
  ["/admin/users", "Tài khoản"],
  ["/admin/audit", "Nhật ký"],
];
function Workspace({ type, children }) {
  const links =
    type === "admin"
      ? adminLinks
      : [
          ["/staff/board", "Bảng công việc"],
          ["/staff/orders", "Danh sách đơn"],
        ];
  return (
    <div className={"work-shell" + (type === "staff" ? " staff-work-shell" : "")}>
      <nav className="work-nav" aria-label="Khu vực làm việc">
        {links.map(([to, text]) => (
          <NavLink key={to} to={to}>
            {text}
          </NavLink>
        ))}
      </nav>
      <main className="work-main">{children}</main>
    </div>
  );
}
function Navigation({ session, onLogout, cartCount }) {
  const role = session.user?.role;
  return (
    <header className="topbar">
      <div className="nav-inner">
        <Link className="brand" to="/">
          Mây Drinks
        </Link>
        <nav className="site-nav" aria-label="Điều hướng chính">
          <NavLink to="/" end>
            Trang chủ
          </NavLink>
          <NavLink to="/menu">Thực đơn</NavLink>
          {role === "customer" && <NavLink to="/orders">Đơn của tôi</NavLink>}
          {role === "staff" && (
            <NavLink to="/staff/board">Đơn hàng</NavLink>
          )}
          {role === "admin" && <NavLink to="/admin/overview">Quản trị</NavLink>}
        </nav>
        <div className="nav-end">
          {role === "customer" && (
            <Link className="btn secondary small" to="/cart">
              Giỏ hàng ({cartCount})
            </Link>
          )}
          {role ? (
            <>
              <Link className="nav-user" to="/account">
                {session.user.name}
              </Link>
              <button
                id="logout-button"
                className="btn secondary small"
                onClick={onLogout}
              >
                Đăng xuất
              </button>
            </>
          ) : (
            <Link className="btn small" to="/login">
              Đăng nhập
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
function AppRoutes({
  session,
  notify,
  signedIn,
  updateUser,
  logout,
  cartVersion,
  onCart,
}) {
  const customer = (children) => (
    <Guard session={session} roles={["customer"]}>
      {children}
    </Guard>
  );
  const staff = (children) => (
    <Guard session={session} roles={["staff"]}>
      <Workspace type="staff">{children}</Workspace>
    </Guard>
  );
  const admin = (children) => (
    <Guard session={session} roles={["admin"]}>
      <Workspace type="admin">{children}</Workspace>
    </Guard>
  );
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/menu" element={<Menu />} />
      <Route
        path="/menu/:id"
        element={<Detail user={session.user} notify={notify} onCart={onCart} />}
      />
      <Route
        path="/cart"
        element={
          <Cart
            user={session.user?.role === "customer" ? session.user : null}
            onCart={onCart}
            version={cartVersion}
          />
        }
      />
      <Route
        path="/checkout"
        element={customer(
          <Checkout user={session.user} notify={notify} onCart={onCart} />,
        )}
      />
      <Route
        path="/orders"
        element={customer(<Orders user={session.user} />)}
      />
      <Route
        path="/orders/:id"
        element={customer(<OrderDetail user={session.user} notify={notify} />)}
      />
      <Route
        path="/login"
        element={
          <Auth user={session.user} signedIn={signedIn} notify={notify} />
        }
      />
      <Route
        path="/register"
        element={
          <Auth
            mode="register"
            user={session.user}
            signedIn={signedIn}
            notify={notify}
          />
        }
      />
      <Route
        path="/forgot-password"
        element={<PasswordPage notify={notify} />}
      />
      <Route
        path="/reset-password"
        element={<PasswordPage reset notify={notify} />}
      />
      <Route
        path="/account"
        element={
          <Guard session={session} roles={["admin", "staff", "customer"]}>
            <Account
              key={session.user?.id}
              user={session.user}
              updated={updateUser}
              logout={logout}
              notify={notify}
            />
          </Guard>
        }
      />
      <Route path="/staff" element={<Navigate to="/staff/board" replace />} />
      <Route
        path="/staff/board"
        element={staff(<StaffBoard notify={notify} />)}
      />
      <Route
        path="/staff/orders"
        element={staff(<StaffOrders />)}
      />
      <Route
        path="/staff/orders/:id"
        element={staff(<StaffOrderDetail notify={notify} />)}
      />
      <Route
        path="/admin"
        element={<Navigate to="/admin/overview" replace />}
      />
      <Route path="/admin/overview" element={admin(<Dashboard />)} />
      <Route
        path="/admin/menu"
        element={admin(<MenuAdmin notify={notify} />)}
      />
      <Route
        path="/admin/options"
        element={admin(<OptionsAdmin notify={notify} />)}
      />
      <Route
        path="/admin/inventory"
        element={admin(<Inventory notify={notify} />)}
      />
      <Route
        path="/admin/recipes"
        element={admin(<Recipes notify={notify} />)}
      />
      <Route
        path="/admin/receipts"
        element={admin(<Receipts notify={notify} />)}
      />
      <Route
        path="/admin/orders"
        element={admin(<Orders user={session.user} />)}
      />
      <Route
        path="/admin/orders/:id"
        element={admin(<OrderDetail user={session.user} notify={notify} />)}
      />
      <Route path="/admin/reports" element={admin(<Reports />)} />
      <Route
        path="/admin/users"
        element={admin(<Users user={session.user} notify={notify} />)}
      />
      <Route
        path="/admin/coupons"
        element={admin(<Coupons notify={notify} />)}
      />
      <Route path="/admin/audit" element={admin(<Audit />)} />
      <Route
        path="*"
        element={
          <main className="container">
            <h1>Không tìm thấy trang</h1>
            <Link to="/">Về trang chủ</Link>
          </main>
        }
      />
    </Routes>
  );
}
export default function App() {
  const [session, setSession] = useState({
      ready: false,
      user: null,
      status: "checking",
      message: "",
    }),
    [cartCount, setCartCount] = useState(0),
    [cartVersion, setCartVersion] = useState(0),
    [toast, setToast] = useState("");
  const navigate = useNavigate(),
    location = useLocation();
  const notify = useCallback((message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3500);
  }, []);
  const connectionCheck = useRef(null);
  const check = useCallback(async () => {
    connectionCheck.current?.abort();
    const controller = new AbortController();
    connectionCheck.current = controller;
    const { signal } = controller;
    setSession((s) => ({ ...s, status: "checking", message: "" }));
    try {
      if (!apiBase) throw new Error("Chưa cấu hình máy chủ API công khai.");
      let health, lastError;
      const deadline = Date.now() + 90000;
      while (Date.now() < deadline && !signal.aborted) {
        try {
          health = await api("/health", {
            signal,
            timeoutMs: Math.min(25000, Math.max(1000, deadline - Date.now())),
          });
          if (health.status === "ok" && health.database === "SQL Server") break;
          throw new Error("Máy chủ không trả trạng thái SQL Server hợp lệ.");
        } catch (e) {
          if (signal.aborted) return;
          lastError = e;
          if (Date.now() + 3000 >= deadline) throw e;
          await new Promise((resolve) => setTimeout(resolve, 3000));
        }
      }
      if (!health || health.status !== "ok" || health.database !== "SQL Server")
        throw lastError || new Error("Máy chủ chưa sẵn sàng.");
      let user = null;
      if (hasToken()) {
        try {
          user = await api("/auth/me", { timeoutMs: 45000, signal });
        } catch (e) {
          if (e.status !== 401) throw e;
        }
      }
      if (signal.aborted) return;
      setSession({ ready: true, user, status: "ok", message: "" });
    } catch (e) {
      if (signal.aborted) return;
      setSession((s) => ({
        ...s,
        ready: true,
        status: "offline",
        message: e.message,
      }));
    }
  }, []);
  useEffect(() => {
    check();
    const handler = () => {
      setSession((s) => ({ ...s, user: null }));
      setCartCount(0);
    };
    window.addEventListener("may-auth-expired", handler);
    return () => {
      connectionCheck.current?.abort();
      window.removeEventListener("may-auth-expired", handler);
    };
  }, [check]);
  useEffect(() => {
    if (!session.ready) return;
    if (session.status !== "ok" || session.user?.role !== "customer") {
      return;
    }
    let active = true;
    api("/cart")
      .then((cart) => {
        if (active)
          setCartCount(
            cart.items.reduce((sum, item) => sum + item.quantity, 0),
          );
      })
      .catch(() => {
        if (active) setCartCount(0);
      });
    return () => {
      active = false;
    };
  }, [
    session.ready,
    session.status,
    session.user?.id,
    session.user?.role,
    cartVersion,
  ]);
  const onCart = () => setCartVersion((v) => v + 1);
  const signedIn = (user) => {
    setSession({ ready: true, user, status: "ok", message: "" });
    onCart();
  };
  const updateUser = (user) => setSession((s) => ({ ...s, user }));
  async function logout() {
    try {
      if (hasToken()) await api("/auth/logout", { method: "POST", body: {} });
    } catch {
      notify(
        "Đã xóa phiên trên trình duyệt; máy chủ có thể chưa nhận yêu cầu đăng xuất.",
      );
    } finally {
      setToken("");
      setSession((s) => ({ ...s, user: null }));
      setCartCount(0);
      navigate("/login");
    }
  }
  return (
    <div className="app">
      <Navigation session={session} onLogout={logout} cartCount={cartCount} />
      {session.status === "ok" ? (
        <AppRoutes
          session={session}
          notify={notify}
          signedIn={signedIn}
          updateUser={updateUser}
          logout={logout}
          cartVersion={cartVersion}
          onCart={onCart}
        />
      ) : (
        <main className="container narrow connection-state">
          <div className="card">
            <span className="eyebrow">Mây Drinks</span>
            {session.status === "checking" ? (
              <>
                <h1>Đang kết nối cửa hàng…</h1>
                <p role="status">
                  Máy chủ miễn phí có thể cần khoảng một phút để khởi động. Vui
                  lòng chờ, trang sẽ tự tải khi kết nối sẵn sàng.
                </p>
                <Busy />
              </>
            ) : (
              <>
                <h1>Chưa thể kết nối cửa hàng</h1>
                <p>
                  Không tải được dữ liệu thực nên tạm thời chưa thể đăng nhập
                  hoặc đặt món. Vui lòng thử lại sau ít phút.
                </p>
                <ErrorBox error={session.message} />
                <button id="retry-api" className="btn" onClick={check}>
                  Kết nối lại
                </button>
              </>
            )}
          </div>
        </main>
      )}
      <footer className="footer">
        <div className="footer-inner">
          <div>
            <strong>Mây Drinks</strong>
            <br />
            Một ngày ngon lành, một ly nước đúng gu.
          </div>
          <span>
            {location.pathname.startsWith("/admin")
              ? "Không gian quản lý"
              : location.pathname.startsWith("/staff")
                ? "Không gian pha chế"
                : "Mây Drinks"}{" "}
            · © 2026
          </span>
        </div>
      </footer>
      {toast && (
        <div role="status" className="toast">
          {toast}
        </div>
      )}
    </div>
  );
}
