import { useState } from "react";
import { Link } from "react-router-dom";
import { money, dateTime } from "../services/api";
import {
  Data,
  Empty,
  ErrorBox,
  Field,
  Status,
  Title,
  useAction,
} from "../components/UI";

const kinds = { size: "Cỡ ly", sugar: "Đường", ice: "Đá", topping: "Topping" };
const flag = (value) => (value ? "Đang dùng" : "Đã ẩn");
function HeadingActions({ title, sub, onCreate, label = "Thêm mới" }) {
  return (
    <Title title={title} sub={sub}>
      <button type="button" className="btn" onClick={onCreate}>
        + {label}
      </button>
    </Title>
  );
}
function RefreshAction({ notify, reload }) {
  return useAction(notify, reload);
}
function Actions({ children }) {
  return <div className="actions">{children}</div>;
}
function BoolField({ id, label, value, onChange }) {
  return (
    <label className="toggle-field" htmlFor={id}>
      <input
        type="checkbox"
        id={id}
        checked={!!value}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );
}
function SaveBar({ busy, onCancel }) {
  return (
    <Actions>
      <button className="btn" disabled={busy} type="submit">
        {busy ? "Đang lưu…" : "Lưu"}
      </button>
      <button className="btn secondary" type="button" onClick={onCancel}>
        Đóng
      </button>
    </Actions>
  );
}
function DashboardContent({ report, alerts }) {
  return (
    <>
      <div className="metric-grid">
        <div className="metric">
          <small>Doanh thu COD đã ghi nhận</small>
          <strong>{money(report.revenue)}</strong>
        </div>
        <div className="metric">
          <small>Đơn tạo trong kỳ</small>
          <strong>{report.order_count}</strong>
        </div>
        <div className="metric">
          <small>Hoàn tất & đã thu tiền</small>
          <strong>{report.completed_paid}</strong>
        </div>
        <div className="metric">
          <small>Nguyên liệu dưới ngưỡng</small>
          <strong>{alerts.low_stock.length}</strong>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h2>Tiến trình đơn</h2>
          {Object.entries(report.states).map(([key, count]) => (
            <div className="summary-row" key={key}>
              <Status value={key} />
              <b>{count}</b>
            </div>
          ))}
          <Link to="/admin/orders">Quản lý đơn hàng →</Link>
        </div>
        <div className="card">
          <h2>Cảnh báo tồn kho</h2>
          {alerts.low_stock.length ? (
            alerts.low_stock.map((i) => (
              <p key={i.id} className="summary-row">
                <span>{i.name}</span>
                <strong>
                  {i.quantity} {i.unit} / tối thiểu {i.minimum}
                </strong>
              </p>
            ))
          ) : (
            <p className="muted">Không có nguyên liệu dưới ngưỡng.</p>
          )}
          <Link to="/admin/inventory">Xem nguyên liệu →</Link>
        </div>
      </div>
      <section className="card" id="at-risk-drinks">
        <h2>Món có nguy cơ tạm hết</h2>
        <p className="muted">
          Ước tính dưới 5 ly theo từng công thức, mức đường/đá cao nhất đang
          bật; chưa gồm topping và chưa giữ nguyên liệu cho đơn chờ.
        </p>
        {alerts.at_risk.length ? (
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Đồ uống</th>
                  <th>Cỡ ly</th>
                  <th>Có thể pha thêm</th>
                </tr>
              </thead>
              <tbody>
                {alerts.at_risk.map((item) => (
                  <tr key={item.drink_id + "-" + item.size}>
                    <td>{item.name}</td>
                    <td>{item.size}</td>
                    <td>
                      {item.cups === 0
                        ? "Không đủ nguyên liệu"
                        : item.cups + " ly"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Chưa có món dưới ngưỡng 5 ly.</p>
        )}
        <Link to="/admin/menu">Kiểm tra trạng thái phục vụ →</Link>
      </section>
    </>
  );
}
export function Dashboard() {
  return (
    <div className="container">
      <Title
        title="Tổng quan cửa hàng"
        sub="Chỉ số lấy trực tiếp từ SQL Server, theo ngày ghi nhận doanh thu."
      />
      <Data path="/admin/reports">
        {(report) => (
          <Data path="/admin/alerts">
            {(alerts) => <DashboardContent report={report} alerts={alerts} />}
          </Data>
        )}
      </Data>
    </div>
  );
}
export function Reports() {
  const [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [range, setRange] = useState("");
  return (
    <div className="container">
      <Title
        title="Thống kê & báo cáo"
        sub="Doanh thu chỉ ghi nhận khi đơn hoàn tất và đã thu COD."
      />
      <div className="filter-row">
        <Field
          id="reports-from"
          label="Từ ngày"
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
        <Field
          id="reports-to"
          label="Đến ngày"
          type="date"
          value={to}
          onChange={(e) => setTo(e.target.value)}
        />
        <button
          className="btn secondary"
          type="button"
          onClick={() =>
            setRange(from && to ? "?from=" + from + "&to=" + to : "")
          }
        >
          Lọc dữ liệu
        </button>
      </div>
      <Data path={"/admin/reports" + range}>
        {(r) => (
          <>
            <div className="metric-grid">
              <div className="metric">
                <small>Doanh thu kỳ này</small>
                <strong>{money(r.revenue)}</strong>
              </div>
              <div className="metric">
                <small>Doanh thu kỳ trước</small>
                <strong>{money(r.previous_revenue)}</strong>
              </div>
              <div className="metric">
                <small>Đơn hoàn tất đã thu</small>
                <strong>{r.completed_paid}</strong>
              </div>
              <div className="metric">
                <small>Trung bình mỗi đơn</small>
                <strong>{money(r.average)}</strong>
              </div>
            </div>
            <div className="grid-2">
              <section className="card">
                <h2>Doanh thu theo ngày</h2>
                {r.daily.map((d) => (
                  <div className="summary-row" key={d.date}>
                    <span>{d.date}</span>
                    <b>{money(d.revenue)}</b>
                  </div>
                ))}
              </section>
              <section className="card">
                <h2>Món bán chạy</h2>
                {r.bestsellers.length ? (
                  r.bestsellers.map((d, i) => (
                    <div className="summary-row" key={i}>
                      <span>
                        {d.name} · {d.quantity} ly
                      </span>
                      <b>{money(d.revenue)}</b>
                    </div>
                  ))
                ) : (
                  <p className="muted">Chưa có đơn COD đã hoàn tất trong kỳ.</p>
                )}
              </section>
              <section className="card">
                <h2>Doanh thu theo danh mục</h2>
                {r.categories.map((d, i) => (
                  <div className="summary-row" key={i}>
                    <span>{d.name}</span>
                    <b>{money(d.revenue)}</b>
                  </div>
                ))}
              </section>
              <section className="card">
                <h2>Nguyên liệu đã sử dụng</h2>
                {r.consumption.map((d, i) => (
                  <div className="summary-row" key={i}>
                    <span>
                      {d.name} · {d.quantity} {d.unit}
                    </span>
                    <b>{money(d.cost)}</b>
                  </div>
                ))}
              </section>
            </div>
          </>
        )}
      </Data>
    </div>
  );
}
function MenuContent({ drinks, categories, options, notify, reload }) {
  const [draft, setDraft] = useState(null);
  const { run, busy, error, setError } = RefreshAction({ notify, reload });
  function edit(row) {
    setError(null);
    setDraft(
      row
        ? { ...row, option_ids: [...row.option_ids] }
        : {
            name: "",
            category_id: categories.find((x) => x.active)?.id || "",
            description: "",
            price: 0,
            image: "/assets/product-0.jpg",
            available: false,
            active: true,
            option_ids: options
              .filter((o) => o.active && o.kind !== "topping")
              .map((o) => o.id),
          },
    );
  }
  return (
    <>
      <HeadingActions
        title="Thực đơn & danh mục"
        sub="Món mới tạm ngừng bán cho đến khi có công thức tương ứng với từng size."
        onCreate={() => edit(null)}
        label="Thêm đồ uống"
      />
      <section className="card">
        <h2>Danh mục</h2>
        <CategoryForm rows={categories} notify={notify} reload={reload} />
      </section>
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            const path = "/admin/drinks" + (draft.id ? "/" + draft.id : "");
            const result = await run(path, draft.id ? "PATCH" : "POST", {
              ...draft,
              price: Number(draft.price),
            });
            if (result) setDraft(null);
          }}
        >
          <h2>{draft.id ? "Chỉnh sửa" : "Thêm"} đồ uống</h2>
          <div className="grid-2">
            <Field
              id="drink-name"
              label="Tên đồ uống"
              required
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
            <Field
              as="select"
              id="drink-category"
              label="Danh mục"
              value={draft.category_id}
              onChange={(e) =>
                setDraft({ ...draft, category_id: e.target.value })
              }
            >
              {categories
                .filter((c) => c.active)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
            </Field>
            <Field
              id="drink-price"
              label="Giá cơ bản (đ)"
              type="number"
              min="0"
              required
              value={draft.price}
              onChange={(e) => setDraft({ ...draft, price: e.target.value })}
            />
            <Field
              id="drink-image"
              label="Đường dẫn ảnh HTTPS hoặc /assets/..."
              required
              value={draft.image}
              onChange={(e) => setDraft({ ...draft, image: e.target.value })}
            />
          </div>
          <Field
            as="textarea"
            id="drink-description"
            label="Mô tả"
            value={draft.description}
            onChange={(e) =>
              setDraft({ ...draft, description: e.target.value })
            }
          />
          <div className="choice-group">
            <strong>Tùy chọn áp dụng cho món</strong>
            <div className="check-grid">
              {options
                .filter((o) => o.active)
                .map((o) => (
                  <BoolField
                    key={o.id}
                    id={"drink-option-" + o.id}
                    label={kinds[o.kind] + " · " + o.name}
                    value={draft.option_ids.includes(o.id)}
                    onChange={(checked) =>
                      setDraft({
                        ...draft,
                        option_ids: checked
                          ? [...draft.option_ids, o.id]
                          : draft.option_ids.filter((id) => id !== o.id),
                      })
                    }
                  />
                ))}
            </div>
          </div>
          <BoolField
            id="drink-active"
            label="Hiển thị trên thực đơn"
            value={draft.active}
            onChange={(active) => setDraft({ ...draft, active })}
          />
          <BoolField
            id="drink-available"
            label="Còn phục vụ"
            value={draft.available}
            onChange={(available) => setDraft({ ...draft, available })}
          />
          <ErrorBox error={error} />
          <SaveBar busy={busy} onCancel={() => setDraft(null)} />
        </form>
      )}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Món</th>
              <th>Danh mục</th>
              <th>Giá</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {drinks.map((d) => (
              <tr key={d.id}>
                <td>
                  <img src={d.image} alt="" /> {d.name}
                </td>
                <td>{d.category}</td>
                <td>{money(d.price)}</td>
                <td>
                  {d.active ? (d.available ? "Đang bán" : "Tạm hết") : "Đã ẩn"}
                </td>
                <td>
                  <button
                    className="btn secondary small"
                    onClick={() => edit(d)}
                  >
                    Sửa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function CategoryForm({ rows, notify, reload }) {
  const [name, setName] = useState(""),
    [editing, setEditing] = useState(null),
    { run, busy, error } = useAction(notify, reload);
  return (
    <>
      <div className="actions">
        {rows.map((c) => (
          <button
            type="button"
            key={c.id}
            className="choice"
            onClick={() => {
              setEditing(c);
              setName(c.name);
            }}
          >
            {c.name} · {flag(c.active)}
          </button>
        ))}
      </div>
      <form
        className="filter-row"
        onSubmit={async (e) => {
          e.preventDefault();
          const result = await run(
            "/admin/categories" + (editing ? "/" + editing.id : ""),
            editing ? "PATCH" : "POST",
            { name, active: true },
          );
          if (result) {
            setName("");
            setEditing(null);
          }
        }}
      >
        <Field
          id="category-name"
          label={editing ? "Sửa danh mục" : "Danh mục mới"}
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="btn small" disabled={busy}>
          {editing ? "Lưu tên" : "Thêm danh mục"}
        </button>
        {editing && (
          <>
            <button
              type="button"
              className="btn secondary small"
              onClick={() => {
                setName("");
                setEditing(null);
              }}
            >
              Hủy sửa
            </button>
            <button
              type="button"
              className="btn danger small"
              disabled={busy}
              onClick={async () => {
                if (
                  window.confirm(
                    "Ẩn danh mục này và các món thuộc danh mục khỏi thực đơn?",
                  )
                ) {
                  if (await run("/admin/categories/" + editing.id, "DELETE")) {
                    setName("");
                    setEditing(null);
                  }
                }
              }}
            >
              Ẩn danh mục
            </button>
          </>
        )}
      </form>
      <ErrorBox error={error} />
    </>
  );
}

export function MenuAdmin({ notify }) {
  const [version, setVersion] = useState(0),
    reload = () => setVersion((x) => x + 1);
  return (
    <div className="container">
      <Data path="/admin/categories" refresh={version}>
        {(categories) => (
          <Data path="/admin/options" refresh={version}>
            {(options) => (
              <Data path="/admin/drinks" refresh={version}>
                {(drinks) => (
                  <MenuContent
                    drinks={drinks}
                    categories={categories}
                    options={options}
                    notify={notify}
                    reload={reload}
                  />
                )}
              </Data>
            )}
          </Data>
        )}
      </Data>
    </div>
  );
}
function InventoryContent({ items, notify, reload, version }) {
  const [draft, setDraft] = useState(null),
    [adjust, setAdjust] = useState(null),
    { run, busy, error, setError } = useAction(notify, reload);
  return (
    <>
      <HeadingActions
        title="Kho nguyên liệu"
        sub="Tồn kho thực tế, ngưỡng cảnh báo và lịch sử điều chỉnh."
        onCreate={() => {
          setDraft({
            name: "",
            unit: "g",
            minimum: 0,
            last_price: 0,
            active: true,
          });
          setAdjust(null);
        }}
        label="Thêm nguyên liệu"
      />
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            if (
              await run(
                "/admin/ingredients" + (draft.id ? "/" + draft.id : ""),
                draft.id ? "PATCH" : "POST",
                {
                  ...draft,
                  minimum: Number(draft.minimum),
                  last_price: Number(draft.last_price),
                },
              )
            )
              setDraft(null);
          }}
        >
          <h2>{draft.id ? "Sửa" : "Thêm"} nguyên liệu</h2>
          <div className="grid-2">
            <Field
              id="ingredient-name"
              label="Tên nguyên liệu"
              required
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
            <Field
              as="select"
              id="ingredient-unit"
              label="Đơn vị"
              disabled={!!draft.id}
              value={draft.unit}
              onChange={(e) => setDraft({ ...draft, unit: e.target.value })}
            >
              {["g", "kg", "ml", "l", "unit"].map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </Field>
            <Field
              id="ingredient-minimum"
              label="Cảnh báo dưới mức"
              type="number"
              min="0"
              step="0.0001"
              required
              value={draft.minimum}
              onChange={(e) => setDraft({ ...draft, minimum: e.target.value })}
            />
            <Field
              id="ingredient-price"
              label="Giá nhập gần nhất (đ / đơn vị)"
              type="number"
              min="0"
              step="0.0001"
              required
              value={draft.last_price}
              onChange={(e) =>
                setDraft({ ...draft, last_price: e.target.value })
              }
            />
          </div>
          <BoolField
            id="ingredient-active"
            label="Đang sử dụng"
            value={draft.active}
            onChange={(active) => setDraft({ ...draft, active })}
          />
          <ErrorBox error={error} />
          <SaveBar busy={busy} onCancel={() => setDraft(null)} />
        </form>
      )}
      {adjust && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            if (
              await run("/admin/ingredients/" + adjust.id + "/adjust", "POST", {
                quantity: Number(adjust.quantity),
                reason: adjust.reason,
              })
            )
              setAdjust(null);
          }}
        >
          <h2>Kiểm kê · {adjust.name}</h2>
          <Field
            id="adjust-quantity"
            label={"Tồn thực tế (" + adjust.unit + ")"}
            type="number"
            min="0"
            step="0.0001"
            required
            value={adjust.quantity}
            onChange={(e) => setAdjust({ ...adjust, quantity: e.target.value })}
          />
          <Field
            id="adjust-reason"
            label="Lý do kiểm kê"
            required
            value={adjust.reason}
            onChange={(e) => setAdjust({ ...adjust, reason: e.target.value })}
          />
          <ErrorBox error={error} />
          <SaveBar busy={busy} onCancel={() => setAdjust(null)} />
        </form>
      )}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Nguyên liệu</th>
              <th>Tồn kho</th>
              <th>Ngưỡng</th>
              <th>Giá nhập</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>{i.name}</td>
                <td>
                  {i.quantity} {i.unit}
                </td>
                <td>
                  {i.minimum} {i.unit}
                </td>
                <td>{money(i.last_price)}</td>
                <td>
                  {i.active
                    ? Number(i.quantity) < Number(i.minimum)
                      ? "Dưới ngưỡng"
                      : "Bình thường"
                    : "Đã ẩn"}
                </td>
                <td>
                  <Actions>
                    <button
                      className="btn secondary small"
                      onClick={() => {
                        setError(null);
                        setDraft({ ...i });
                        setAdjust(null);
                      }}
                    >
                      Sửa
                    </button>
                    <button
                      className="btn secondary small"
                      onClick={() => {
                        setError(null);
                        setAdjust({ ...i, reason: "" });
                        setDraft(null);
                      }}
                    >
                      Kiểm kê
                    </button>
                  </Actions>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="section-gap">
        <h2>Lịch sử xuất nhập</h2>
        <Data path="/admin/inventory-transactions" refresh={version}>
          {(rows) =>
            rows.length ? (
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Ngày</th>
                      <th>Nguyên liệu</th>
                      <th>Loại</th>
                      <th>Thay đổi</th>
                      <th>Tồn sau</th>
                      <th>Lý do</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.slice(0, 100).map((row) => (
                      <tr key={row.id}>
                        <td>{dateTime(row.created_at)}</td>
                        <td>{row.ingredient}</td>
                        <td>{row.kind}</td>
                        <td>
                          {row.delta} {row.unit}
                        </td>
                        <td>
                          {row.balance} {row.unit}
                        </td>
                        <td>{row.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>Chưa có biến động kho.</Empty>
            )
          }
        </Data>
      </div>
    </>
  );
}
export function Inventory({ notify }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/ingredients" refresh={version}>
        {(items) => (
          <InventoryContent
            items={items}
            notify={notify}
            version={version}
            reload={() => setVersion((x) => x + 1)}
          />
        )}
      </Data>
    </div>
  );
}
