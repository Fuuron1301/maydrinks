import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api, money, dateTime, choiceText, labels } from "../services/api";
import {
  Data,
  Empty,
  ErrorBox,
  Field,
  Status,
  Title,
  useAction,
} from "../components/UI";

const photo = (item) => item?.image || "/assets/product-0.jpg";
export function ProductCard({ drink }) {
  return (
    <article className="product-card">
      <Link to={"/menu/" + drink.id}>
        <img src={photo(drink)} alt={drink.name} loading="lazy" />
      </Link>
      <div className="product-card-body">
        <small>{drink.category}</small>
        <h3>
          <Link to={"/menu/" + drink.id}>{drink.name}</Link>
        </h3>
        <div className="row">
          <span className="price">{money(drink.price)}</span>
          <Link className="btn small secondary" to={"/menu/" + drink.id}>
            Xem món
          </Link>
        </div>
      </div>
    </article>
  );
}
export function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <span className="eyebrow">Pha chút tươi mới vào ngày của bạn</span>
            <h1>
              Chạm vị ngon.
              <br />
              Vui cùng Mây.
            </h1>
            <p>
              Chọn ly nước bạn thích, tùy chỉnh theo gu của mình và theo dõi đơn
              hàng dễ dàng.
            </p>
            <Link className="btn" to="/menu">
              Khám phá thực đơn →
            </Link>
          </div>
          <img
            className="hero-img"
            src="/assets/hero-drinks.jpg"
            alt="Những ly nước tươi ngon tại Mây Drinks"
          />
        </div>
      </section>
      <main className="container">
        <section className="home-section">
          <div className="section-head">
            <div>
              <span className="eyebrow">Thực đơn nhà Mây</span>
              <h2>Chọn một ly đúng gu</h2>
            </div>
            <Link to="/menu">Xem thực đơn →</Link>
          </div>
          <Data path="/catalog">
            {(data) =>
              data.drinks.some((d) => d.available) ? (
                <div className="product-grid">
                  {data.drinks
                    .filter((d) => d.available)
                    .slice(0, 4)
                    .map((d) => (
                      <ProductCard key={d.id} drink={d} />
                    ))}
                </div>
              ) : (
                <Empty>Thực đơn chưa có món khả dụng.</Empty>
              )
            }
          </Data>
        </section>
        <section className="home-section grid-2">
          <div className="card">
            <h2>Mỗi ly, một chút chăm chút</h2>
            <p>
              Điều chỉnh size, đá, đường và topping trước khi bạn xác nhận đơn.
              Giá và nguyên liệu được tính trên hệ thống.
            </p>
            <Link className="btn secondary" to="/menu">
              Chọn món ngay
            </Link>
          </div>
          <img
            className="detail-photo story-photo"
            src="/assets/our-story.jpg"
            alt="Không gian pha chế của Mây"
            loading="lazy"
          />
        </section>
      </main>
    </>
  );
}
export function Menu() {
  const [params] = useSearchParams(),
    [query, setQuery] = useState(""),
    [category, setCategory] = useState(params.get("category") || "");
  return (
    <main className="container">
      <Title
        title="Thực đơn nhà Mây"
        sub="Chọn món và điều chỉnh cho vừa gu bạn."
      />
      <Data path="/catalog">
        {(data) => (
          <>
            <div className="filter-row">
              <input
                className="control"
                id="menu-search"
                aria-label="Tìm đồ uống"
                placeholder="Tìm theo tên món…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select
                className="control"
                id="menu-category"
                aria-label="Danh mục"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="">Tất cả danh mục</option>
                {data.categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            {data.drinks.filter(
              (d) =>
                (!category || d.category_id === category) &&
                d.name.toLowerCase().includes(query.trim().toLowerCase()),
            ).length ? (
              <div className="product-grid">
                {data.drinks
                  .filter(
                    (d) =>
                      (!category || d.category_id === category) &&
                      d.name.toLowerCase().includes(query.trim().toLowerCase()),
                  )
                  .map((d) => (
                    <ProductCard key={d.id} drink={d} />
                  ))}
              </div>
            ) : (
              <Empty>Không tìm thấy đồ uống phù hợp.</Empty>
            )}
          </>
        )}
      </Data>
    </main>
  );
}
function Options({ label, options, selected, onChange, multiple = false }) {
  return (
    <div className="choice-group">
      <strong>{label}</strong>
      <div className="choice-list">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            className={
              "choice " +
              ((multiple ? selected.includes(o.id) : selected === o.id)
                ? "active"
                : "")
            }
            aria-pressed={
              multiple ? selected.includes(o.id) : selected === o.id
            }
            onClick={() => onChange(o.id)}
          >
            {o.name}
            {o.surcharge ? " +" + money(o.surcharge) : ""}
          </button>
        ))}
      </div>
    </div>
  );
}
function ProductCustomizer({ drink, options, user, notify, onCart }) {
  const navigate = useNavigate();
  const available = (kind) =>
    options.filter(
      (o) => o.kind === kind && o.active && drink.option_ids.includes(o.id),
    );
  const [choice, setChoice] = useState({
    size: "",
    sugar: "",
    ice: "",
    toppings: [],
  });
  const [quantity, setQuantity] = useState(1),
    [error, setError] = useState(null),
    [busy, setBusy] = useState(false),
    [quote, setQuote] = useState(null);
  const selected = {
    size: available("size").some((o) => o.id === choice.size)
      ? choice.size
      : available("size")[0]?.id,
    sugar: available("sugar").some((o) => o.id === choice.sugar)
      ? choice.sugar
      : available("sugar")[0]?.id,
    ice: available("ice").some((o) => o.id === choice.ice)
      ? choice.ice
      : available("ice")[0]?.id,
    toppings: choice.toppings,
  };
  const payload = { drink_id: drink.id, quantity, choices: selected };
  const change = (kind, id) => {
    setQuote(null);
    setError(null);
    setChoice((old) => ({
      ...old,
      [kind]:
        kind === "toppings"
          ? old.toppings.includes(id)
            ? old.toppings.filter((x) => x !== id)
            : old.toppings.length < 3
              ? [...old.toppings, id]
              : old.toppings
          : id,
    }));
  };
  const toppingsKey = selected.toppings.join(",");
  useEffect(() => {
    let active = true;
    if (!selected.size || !selected.sugar || !selected.ice || !drink.available)
      return;
    const timeout = setTimeout(() => {
      api("/quote", {
        method: "POST",
        body: {
          drink_id: drink.id,
          quantity,
          choices: {
            size: selected.size,
            sugar: selected.sugar,
            ice: selected.ice,
            toppings: toppingsKey ? toppingsKey.split(",") : [],
          },
        },
      })
        .then((result) => {
          if (active) {
            setQuote(result);
            setError(null);
          }
        })
        .catch((e) => {
          if (active) {
            setQuote(null);
            setError(e);
          }
        });
    }, 260);
    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [
    drink.id,
    drink.available,
    quantity,
    selected.size,
    selected.sugar,
    selected.ice,
    toppingsKey,
  ]);
  async function add() {
    if (!user) {
      navigate("/login?next=" + encodeURIComponent("/menu/" + drink.id));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api("/cart/items", { method: "POST", body: payload });
      onCart();
      notify("Đã thêm vào giỏ hàng");
      navigate("/cart");
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Link to="/menu" className="eyebrow">
        ← Thực đơn
      </Link>
      <div className="detail-grid detail-view">
        <img className="detail-photo" src={photo(drink)} alt={drink.name} />
        <div className="card">
          <small>{drink.category}</small>
          <h1 className="detail-title">{drink.name}</h1>
          <p className="muted">{drink.description}</p>
          {!drink.available && (
            <ErrorBox error="Món hiện tạm hết. Vui lòng chọn món khác." />
          )}
          <Options
            label="Cỡ ly"
            options={available("size")}
            selected={selected.size}
            onChange={(x) => change("size", x)}
          />
          <Options
            label="Đường"
            options={available("sugar")}
            selected={selected.sugar}
            onChange={(x) => change("sugar", x)}
          />
          <Options
            label="Đá"
            options={available("ice")}
            selected={selected.ice}
            onChange={(x) => change("ice", x)}
          />
          <Options
            label="Topping (tối đa 3)"
            options={available("topping")}
            multiple
            selected={selected.toppings}
            onChange={(x) => change("toppings", x)}
          />
          <Field
            label="Số lượng"
            id="detail-quantity"
            type="number"
            min="1"
            max="99"
            value={quantity}
            onChange={(e) => {
              setQuote(null);
              setQuantity(
                Math.max(
                  1,
                  Math.min(99, Math.floor(Number(e.target.value) || 1)),
                ),
              );
            }}
          />
          <p className="price">
            {quote
              ? money(quote.unit_price * quantity)
              : !drink.available
                ? "Tạm ngừng phục vụ"
                : error
                  ? "Chưa thể báo giá"
                  : "Đang tính giá…"}
          </p>
          <ErrorBox error={error} />
          <button
            id="add-to-cart"
            type="button"
            className="btn full"
            disabled={
              busy ||
              !drink.available ||
              !quote ||
              (user && user.role !== "customer")
            }
            onClick={add}
          >
            {user && user.role !== "customer"
              ? "Đặt hàng bằng tài khoản khách hàng"
              : busy
                ? "Đang thêm…"
                : "Thêm vào giỏ"}
          </button>
        </div>
      </div>
    </>
  );
}
export function Detail({ user, notify, onCart }) {
  const { id } = useParams();
  return (
    <main className="container">
      <Data path="/catalog">
        {(catalog) => {
          const drink = catalog.drinks.find((d) => d.id === id);
          return drink ? (
            <ProductCustomizer
              key={id}
              drink={drink}
              options={catalog.options}
              user={user}
              notify={notify}
              onCart={onCart}
            />
          ) : (
            <>
              <h1>Không tìm thấy món</h1>
              <Link to="/menu">Về thực đơn</Link>
            </>
          );
        }}
      </Data>
    </main>
  );
}
export function Cart({ user, onCart, version }) {
  return (
    <main className="container narrow">
      <Title title="Giỏ hàng" sub="Xem lại món trước khi đặt." />
      {!user ? (
        <Empty>
          <Link to="/login?next=%2Fcart">Đăng nhập</Link> để lưu giỏ hàng.
        </Empty>
      ) : (
        <Data path="/cart" refresh={version}>
          {(cart, reload) =>
            cart.items.length ? (
              <div className="grid-2">
                <div className="card">
                  <h2>Món đã chọn</h2>
                  {cart.items.map((item) => (
                    <CartLine
                      key={item.id}
                      item={item}
                      reload={() => {
                        reload();
                        onCart();
                      }}
                    />
                  ))}
                </div>
                <div className="card aside-card">
                  <h2>Tạm tính</h2>
                  <div className="summary-row total">
                    <span>{cart.items.length} dòng món</span>
                    <b>{money(cart.subtotal)}</b>
                  </div>
                  {cart.items.some((i) => !i.valid) && (
                    <ErrorBox error="Có món không hợp lệ. Hãy xóa hoặc chọn lại trước khi đặt hàng." />
                  )}
                  {cart.items.every((i) => i.valid) ? (
                    <Link className="btn full" to="/checkout">
                      Tiến hành đặt hàng
                    </Link>
                  ) : (
                    <button className="btn full" disabled>
                      Vui lòng sửa giỏ hàng
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <Empty>
                Giỏ đang trống. <Link to="/menu">Khám phá thực đơn</Link>
              </Empty>
            )
          }
        </Data>
      )}
    </main>
  );
}
function CartLine({ item, reload }) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(null);
  async function change(method, body) {
    setBusy(true);
    setError(null);
    try {
      await api("/cart/items/" + item.id, { method, body });
      reload();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="line-item">
      <img src={photo(item)} alt="" />
      <div>
        <h3>{item.name}</h3>
        <p>{item.valid ? choiceText(item.choices) : item.error}</p>
        <div className="actions">
          <button
            aria-label={"Giảm số lượng " + item.name}
            className="btn secondary small"
            disabled={busy || item.quantity <= 1}
            onClick={() => change("PATCH", { quantity: item.quantity - 1 })}
          >
            −
          </button>
          <span>{item.quantity}</span>
          <button
            aria-label={"Tăng số lượng " + item.name}
            className="btn secondary small"
            disabled={busy || item.quantity >= 99}
            onClick={() => change("PATCH", { quantity: item.quantity + 1 })}
          >
            +
          </button>
          <button
            className="btn danger small"
            disabled={busy}
            onClick={() => change("DELETE")}
          >
            Xóa
          </button>
        </div>
        <ErrorBox error={error} />
      </div>
      <b className="price">{money(item.unit_price * item.quantity)}</b>
    </div>
  );
}
export function Checkout({ user, onCart, notify }) {
  const navigate = useNavigate(),
    [form, setForm] = useState({
      recipient: user.name || "",
      phone: user.phone || "",
      address: user.address || "",
      note: "",
      coupon: "",
    }),
    [error, setError] = useState(null),
    [busy, setBusy] = useState(false),
    [key] = useState(
      () =>
        sessionStorage.getItem("maydrinks.checkout." + user.id) ||
        crypto.randomUUID(),
    ),
    [pending, setPending] = useState(
      () => !!sessionStorage.getItem("maydrinks.checkout." + user.id),
    );
  function accepted(order) {
    sessionStorage.removeItem("maydrinks.checkout." + user.id);
    onCart();
    notify("Đã xác nhận đơn " + order.code);
    navigate("/orders/" + order.id);
  }
  async function recover() {
    setBusy(true);
    setError(null);
    try {
      accepted(await api("/orders/request/" + encodeURIComponent(key)));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="container">
      <Title
        title="Xác nhận đơn hàng"
        sub="Thanh toán khi nhận (COD) · Đơn chỉ được tạo khi đủ nguyên liệu."
      />
      {pending && (
        <section className="card" id="checkout-recovery">
          <h2>Kiểm tra lần gửi đơn trước</h2>
          <p>
            Nếu mạng ngắt khi gửi, đơn có thể đã được tạo. Kiểm tra trước; khi
            gửi lại, hệ thống giữ cùng mã yêu cầu để không tạo đơn trùng.
          </p>
          <button
            id="recover-checkout"
            type="button"
            className="btn secondary"
            disabled={busy}
            onClick={recover}
          >
            Kiểm tra đơn đã gửi
          </button>
          <ErrorBox error={error} />
        </section>
      )}
      <Data path="/cart">
        {(cart) =>
          cart.items.length ? (
            <form
              className="grid-2"
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                setError(null);
                sessionStorage.setItem("maydrinks.checkout." + user.id, key);
                setPending(true);
                try {
                  accepted(
                    await api("/orders", {
                      method: "POST",
                      headers: { "Idempotency-Key": key },
                      body: form,
                    }),
                  );
                } catch (err) {
                  setError(err);
                  if (err.status >= 400 && err.status < 500) {
                    sessionStorage.removeItem("maydrinks.checkout." + user.id);
                    setPending(false);
                  }
                } finally {
                  setBusy(false);
                }
              }}
            >
              <div className="card">
                <h2>Thông tin nhận hàng</h2>
                <Field
                  id="checkout-recipient"
                  label="Người nhận"
                  required
                  value={form.recipient}
                  onChange={(e) =>
                    setForm({ ...form, recipient: e.target.value })
                  }
                />
                <Field
                  id="checkout-phone"
                  label="Số điện thoại"
                  required
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
                <Field
                  id="checkout-address"
                  label="Địa chỉ giao hàng"
                  required
                  value={form.address}
                  onChange={(e) =>
                    setForm({ ...form, address: e.target.value })
                  }
                />
                <Field
                  id="checkout-note"
                  label="Ghi chú"
                  value={form.note}
                  onChange={(e) => setForm({ ...form, note: e.target.value })}
                />
                <Field
                  id="checkout-coupon"
                  label="Mã ưu đãi (nếu có)"
                  value={form.coupon}
                  onChange={(e) => setForm({ ...form, coupon: e.target.value })}
                />
              </div>
              <div className="card aside-card">
                <h2>Đơn của bạn</h2>
                {cart.items.map((i) => (
                  <div key={i.id} className="summary-row">
                    <span>
                      {i.quantity} × {i.name}
                    </span>
                    <b>{money(i.unit_price * i.quantity)}</b>
                  </div>
                ))}
                <div className="summary-row total">
                  <span>Tạm tính</span>
                  <b>{money(cart.subtotal)}</b>
                </div>
                <p className="muted">
                  COD · Thanh toán khi nhận hàng. Mã ưu đãi sẽ được kiểm tra
                  trước khi tạo đơn.
                </p>
                <ErrorBox error={error} />
                <button
                  id="checkout-submit"
                  className="btn full"
                  disabled={busy || cart.items.some((i) => !i.valid)}
                >
                  {busy ? "Đang gửi đơn…" : "Đặt hàng"}
                </button>
              </div>
            </form>
          ) : (
            <Empty>
              Giỏ hàng trống. <Link to="/menu">Chọn món</Link>
            </Empty>
          )
        }
      </Data>
    </main>
  );
}
export function Orders({ user }) {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    if (user.role === "customer") return undefined;
    const timer = window.setInterval(() => setVersion((x) => x + 1), 10000);
    return () => window.clearInterval(timer);
  }, [user.role]);
  return (
    <main className="container">
      <Title
        title={user.role === "customer" ? "Đơn của tôi" : "Danh sách đơn"}
        sub="Theo dõi trạng thái và chi tiết đơn hàng. Nhấn tải lại để lấy tiến trình mới nhất."
      >
        <button
          id="refresh-orders"
          type="button"
          className="btn secondary"
          onClick={() => setVersion((x) => x + 1)}
        >
          Tải lại đơn
        </button>
      </Title>
      <Data path="/orders" refresh={version}>
        {(orders) =>
          orders.length ? (
            <div className="card">
              {orders.map((o) => (
                <div key={o.id} className="order-card">
                  <div className="row">
                    <b>{o.code}</b>
                    <Status value={o.status} />
                  </div>
                  <p>
                    {dateTime(o.created_at)} · {o.recipient} · {o.items.length}{" "}
                    dòng món
                  </p>
                  <div className="row">
                    <strong className="price">{money(o.total)}</strong>
                    <Link
                      className="btn secondary small"
                      to={
                        (user.role === "customer"
                          ? "/orders/"
                          : user.role === "admin"
                            ? "/admin/orders/"
                            : "/staff/orders/") + o.id
                      }
                    >
                      Xem chi tiết
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty>Chưa có đơn hàng.</Empty>
          )
        }
      </Data>
    </main>
  );
}
function CustomerCancellation({ order, busy, run }) {
  const remainingAtReceipt = Math.max(
    0,
    Date.parse(order.cancel_deadline) - Date.parse(order.server_time),
  );
  const [clock, setClock] = useState(() => ({
    serverTime: order.server_time,
    elapsed: 0,
  }));
  useEffect(() => {
    const receivedAt = performance.now();
    const update = () => setClock({
      serverTime: order.server_time,
      elapsed: performance.now() - receivedAt,
    });
    const timer = window.setInterval(update, 250);
    const onVisible = () => update();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [order.server_time, order.cancel_deadline]);
  const elapsed = clock.serverTime === order.server_time ? clock.elapsed : 0;
  const seconds = Math.max(0, Math.ceil((remainingAtReceipt - elapsed) / 1000));
  const countdown = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  return (
    <div>
      <p className="muted">
        {seconds > 0
          ? `Còn ${countdown} để hủy. Chỉ được hủy trong 60 giây sau khi đặt và trước khi nhận pha.`
          : "Đã hết thời hạn hủy đơn 60 giây."}
      </p>
      <button
        id="cancel-customer-order"
        disabled={busy || seconds === 0}
        className="btn danger"
        onClick={() => {
          if (window.confirm("Bạn muốn hủy đơn này?"))
            run("/orders/" + order.id + "/cancel", "POST", {
              reason: "Khách hàng yêu cầu hủy",
            });
        }}
      >
        Hủy đơn
      </button>
    </div>
  );
}

export function OrderDetail({ user, notify }) {
  const { id } = useParams(),
    [version, setVersion] = useState(0),
    { run, busy, error } = useAction(notify, () => setVersion((x) => x + 1));
  return (
    <main className="container narrow">
      <Data path={"/orders/" + id} refresh={version}>
        {(o) => (
          <>
            <Title title={"Đơn " + o.code} sub={dateTime(o.created_at)}>
              <Status value={o.status} />
              <button
                id="refresh-order-detail"
                type="button"
                className="btn secondary small"
                disabled={busy}
                onClick={() => setVersion((x) => x + 1)}
              >
                Tải lại trạng thái
              </button>
            </Title>
            {o.status === "cancelled" && (
              <div className="order-cancelled-banner" role="status">
                <span aria-hidden="true">⊗</span>Đơn hàng đã được hủy thành công.
              </div>
            )}
            <div className="grid-2">
              <div className="card">
                <h2>Món đã đặt</h2>
                {o.items.map((i) => (
                  <div key={i.id} className="line-item">
                    <img src={photo(i)} alt="" />
                    <div>
                      <h3>{i.name}</h3>
                      <p>{choiceText(i.choices)}</p>
                      <p>
                        {i.quantity} × {money(i.unit_price)}
                      </p>
                    </div>
                    <strong>{money(i.quantity * i.unit_price)}</strong>
                  </div>
                ))}
                <div className="summary-row">
                  <span>Tạm tính</span>
                  <b>{money(o.subtotal)}</b>
                </div>
                <div className="summary-row">
                  <span>Giảm giá</span>
                  <b>−{money(o.discount)}</b>
                </div>
                <div className="summary-row total">
                  <span>Tổng COD</span>
                  <b>{money(o.total)}</b>
                </div>
              </div>
              <div className="stack">
                <div className="card">
                  <h2>Thông tin giao hàng</h2>
                  <p>
                    {o.recipient}
                    <br />
                    {o.phone}
                    <br />
                    {o.address}
                  </p>
                  {o.note && <p>{o.note}</p>}
                  <p>
                    Thanh toán:{" "}
                    {o.payment?.status === "paid"
                      ? "Đã thu tiền"
                      : "Chưa thu tiền"}
                  </p>
                </div>
                <div className="card">
                  <h2>Tiến trình</h2>
                  <ul className="timeline">
                    {o.history.map((h) => (
                      <li key={h.id}>
                        <strong>{labels[h.status] || h.status}</strong>
                        <small>
                          {dateTime(h.created_at)} · {h.actor}
                        </small>
                        <small>{h.note}</small>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="card">
                  <h2>Thao tác</h2>
                  <ErrorBox error={error} />
                  {user.role === "customer" && o.status === "pending" && (
                    <CustomerCancellation order={o} busy={busy} run={run} />
                  )}
                  {["admin", "staff"].includes(user.role) && (
                    <div className="actions">
                      {{
                        pending: "preparing",
                        preparing: "ready",
                        ready: "completed",
                      }[o.status] && (
                        <button
                          disabled={busy}
                          className="btn"
                          onClick={() =>
                            run("/orders/" + o.id + "/status", "POST", {
                              expected_status: o.status,
                              status: {
                                pending: "preparing",
                                preparing: "ready",
                                ready: "completed",
                              }[o.status],
                            })
                          }
                        >
                          Chuyển sang{" "}
                          {
                            labels[
                              {
                                pending: "preparing",
                                preparing: "ready",
                                ready: "completed",
                              }[o.status]
                            ]
                          }
                        </button>
                      )}
                      {o.payment?.status !== "paid" &&
                        ["ready", "completed"].includes(
                          o.status,
                        ) && (
                          <button
                            disabled={busy}
                            className="btn secondary"
                            onClick={() =>
                              run("/orders/" + o.id + "/payment", "POST", {
                                amount: o.total,
                              })
                            }
                          >
                            Xác nhận thu COD
                          </button>
                        )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </Data>
    </main>
  );
}
