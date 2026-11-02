import { useState } from "react";
import { dateTime, money } from "../services/api";
import {
  Data,
  Empty,
  ErrorBox,
  Field,
  Title,
  useAction,
} from "../components/UI";

const kinds = { size: "Cỡ ly", sugar: "Đường", ice: "Đá", topping: "Topping" };
const units = ["g", "kg", "ml", "l", "unit"];
const newLine = () => ({
  ingredient_id: "",
  quantity: 1,
  unit: "g",
  scales_with: "none",
});
function Select({
  id,
  label,
  value,
  onChange,
  items,
  valueKey = "id",
  textKey = "name",
  empty = false,
  disabled = false,
}) {
  return (
    <Field
      as="select"
      id={id}
      label={label}
      value={value}
      disabled={disabled}
      required
      onChange={(e) => onChange(e.target.value)}
    >
      {empty && <option value="">Chọn...</option>}
      {items.map((row) => (
        <option key={row[valueKey]} value={row[valueKey]}>
          {row[textKey]}
        </option>
      ))}
    </Field>
  );
}
function LineEditor({ lines, ingredients, onChange, topping = false }) {
  return (
    <div className="stack">
      {lines.map((line, index) => (
        <div className="receipt-line" key={index}>
          <Select
            id={"line-ingredient-" + index}
            label="Nguyên liệu"
            items={ingredients.filter(
              (i) => i.active || i.id === line.ingredient_id,
            )}
            value={line.ingredient_id}
            onChange={(value) =>
              onChange(
                lines.map((x, j) =>
                  j === index
                    ? {
                        ...x,
                        ingredient_id: value,
                        unit:
                          ingredients.find((i) => i.id === value)?.unit ||
                          x.unit,
                      }
                    : x,
                ),
              )
            }
            empty
          />
          <Field
            id={"line-quantity-" + index}
            label="Định lượng"
            type="number"
            min="0.0001"
            step="0.0001"
            required
            value={line.quantity}
            onChange={(e) =>
              onChange(
                lines.map((x, j) =>
                  j === index ? { ...x, quantity: e.target.value } : x,
                ),
              )
            }
          />
          <Select
            id={"line-unit-" + index}
            label="Đơn vị"
            items={units.map((u) => ({ id: u, name: u }))}
            value={line.unit}
            onChange={(value) =>
              onChange(
                lines.map((x, j) => (j === index ? { ...x, unit: value } : x)),
              )
            }
          />
          {!topping && (
            <Select
              id={"line-scale-" + index}
              label="Thay đổi theo"
              items={[
                { id: "none", name: "Không" },
                { id: "sugar", name: "Đường" },
                { id: "ice", name: "Đá" },
              ]}
              value={line.scales_with || "none"}
              onChange={(value) =>
                onChange(
                  lines.map((x, j) =>
                    j === index ? { ...x, scales_with: value } : x,
                  ),
                )
              }
            />
          )}
          <button
            type="button"
            className="btn danger small"
            onClick={() => onChange(lines.filter((_, j) => index !== j))}
          >
            Xóa
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn secondary small"
        onClick={() => onChange([...lines, newLine()])}
      >
        + Dòng nguyên liệu
      </button>
    </div>
  );
}
function OptionContent({ rows, ingredients, notify, reload }) {
  const [draft, setDraft] = useState(null),
    { run, busy, error } = useAction(notify, reload);
  const select = (row) =>
    setDraft(
      row
        ? { ...row, ingredients: row.ingredients.map((x) => ({ ...x })) }
        : {
            kind: "size",
            name: "",
            surcharge: 0,
            factor: 1,
            active: true,
            ingredients: [],
          },
    );
  return (
    <>
      <Title
        title="Tùy chọn đồ uống"
        sub="Cỡ ly, mức đường/đá và topping có thể ảnh hưởng giá và định lượng."
      >
        <button className="btn" onClick={() => select(null)}>
          + Thêm tùy chọn
        </button>
      </Title>
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            const result = await run(
              "/admin/options" + (draft.id ? "/" + draft.id : ""),
              draft.id ? "PATCH" : "POST",
              {
                kind: draft.kind,
                name: draft.name,
                surcharge: Number(draft.surcharge),
                factor: Number(draft.factor),
                active: draft.active,
                ...(draft.kind === "topping"
                  ? {
                      ingredients: draft.ingredients.map((x) => ({
                        ingredient_id: x.ingredient_id,
                        quantity: Number(x.quantity),
                        unit: x.unit,
                      })),
                    }
                  : {}),
              },
            );
            if (result) setDraft(null);
          }}
        >
          <h2>{draft.id ? "Chỉnh sửa" : "Thêm mới"}</h2>
          <div className="grid-2">
            <Select
              id="option-kind"
              label="Loại"
              disabled={!!draft.id}
              value={draft.kind}
              onChange={(value) =>
                setDraft({ ...draft, kind: value, ingredients: [] })
              }
              items={Object.entries(kinds).map(([id, name]) => ({ id, name }))}
            />
            <Field
              id="option-name"
              label="Tên tùy chọn"
              required
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
            <Field
              id="option-surcharge"
              label="Phụ thu (đ)"
              type="number"
              min="0"
              required
              value={draft.surcharge}
              onChange={(e) =>
                setDraft({ ...draft, surcharge: e.target.value })
              }
            />
            <Field
              id="option-factor"
              label="Hệ số nguyên liệu"
              type="number"
              min="0"
              max="3"
              step="0.0001"
              required
              value={draft.factor}
              onChange={(e) => setDraft({ ...draft, factor: e.target.value })}
            />
          </div>
          {draft.kind === "topping" && (
            <>
              <h3>Nguyên liệu topping</h3>
              <LineEditor
                topping
                lines={draft.ingredients}
                ingredients={ingredients}
                onChange={(lines) => setDraft({ ...draft, ingredients: lines })}
              />
            </>
          )}
          <label className="toggle-field">
            <input
              type="checkbox"
              checked={draft.active}
              onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
            />
            Đang dùng
          </label>
          <ErrorBox error={error} />
          <div className="actions">
            <button className="btn" disabled={busy}>
              Lưu
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setDraft(null)}
            >
              Đóng
            </button>
          </div>
        </form>
      )}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Loại</th>
              <th>Tên</th>
              <th>Phụ thu</th>
              <th>Hệ số</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.id}>
                <td>{kinds[o.kind]}</td>
                <td>{o.name}</td>
                <td>{money(o.surcharge)}</td>
                <td>{o.factor}</td>
                <td>{o.active ? "Đang dùng" : "Đã ẩn"}</td>
                <td>
                  <button
                    className="btn secondary small"
                    onClick={() => select(o)}
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
export function OptionsAdmin({ notify }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/options" refresh={version}>
        {(rows) => (
          <Data path="/admin/ingredients" refresh={version}>
            {(ingredients) => (
              <OptionContent
                rows={rows}
                ingredients={ingredients}
                notify={notify}
                reload={() => setVersion((x) => x + 1)}
              />
            )}
          </Data>
        )}
      </Data>
    </div>
  );
}
function RecipeContent({ rows, drinks, options, ingredients, notify, reload }) {
  const [draft, setDraft] = useState(null),
    { run, busy, error } = useAction(notify, reload);
  const sizes = options.filter(
    (o) =>
      o.kind === "size" &&
      o.active &&
      drinks.find((d) => d.id === draft?.drink_id)?.option_ids.includes(o.id),
  );
  const edit = (row) =>
    setDraft(
      row
        ? { ...row, lines: row.lines.map((x) => ({ ...x })) }
        : {
            drink_id: drinks.find((d) => d.active)?.id || "",
            size_id: "",
            name: "",
            instructions: "",
            active: true,
            lines: [],
          },
    );
  return (
    <>
      <Title
        title="Công thức pha chế"
        sub="Mỗi đồ uống và cỡ ly cần một công thức định lượng từ nguyên liệu có trong kho."
      >
        <button className="btn" onClick={() => edit(null)}>
          + Thêm công thức
        </button>
      </Title>
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            const result = await run(
              "/admin/recipes" + (draft.id ? "/" + draft.id : ""),
              draft.id ? "PATCH" : "POST",
              {
                ...draft,
                size_id: draft.size_id || sizes[0]?.id,
                lines: draft.lines.map((x) => ({
                  ingredient_id: x.ingredient_id,
                  quantity: Number(x.quantity),
                  unit: x.unit,
                  scales_with: x.scales_with || "none",
                })),
              },
            );
            if (result) setDraft(null);
          }}
        >
          <h2>{draft.id ? "Chỉnh sửa" : "Thêm"} công thức</h2>
          <div className="grid-2">
            <Select
              id="recipe-drink"
              label="Đồ uống"
              value={draft.drink_id}
              onChange={(value) =>
                setDraft({ ...draft, drink_id: value, size_id: "" })
              }
              items={drinks.filter((d) => d.active)}
            />
            <Select
              id="recipe-size"
              label="Cỡ ly"
              value={draft.size_id || sizes[0]?.id || ""}
              onChange={(value) => setDraft({ ...draft, size_id: value })}
              items={sizes}
            />
            <Field
              id="recipe-name"
              label="Tên công thức"
              required
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <Field
            as="textarea"
            id="recipe-instructions"
            label="Hướng dẫn pha chế"
            value={draft.instructions}
            onChange={(e) =>
              setDraft({ ...draft, instructions: e.target.value })
            }
          />
          <h3>Định lượng nguyên liệu</h3>
          <LineEditor
            lines={draft.lines}
            ingredients={ingredients}
            onChange={(lines) => setDraft({ ...draft, lines })}
          />
          <label className="toggle-field" htmlFor="recipe-active">
            <input
              id="recipe-active"
              type="checkbox"
              checked={draft.active}
              onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
            />
            Đang sử dụng công thức
          </label>
          <ErrorBox error={error} />
          <div className="actions">
            <button className="btn" disabled={busy}>
              Lưu công thức
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setDraft(null)}
            >
              Đóng
            </button>
          </div>
        </form>
      )}
      {!draft && <ErrorBox error={error} />}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Đồ uống</th>
              <th>Cỡ</th>
              <th>Công thức</th>
              <th>Định lượng</th>
              <th>Giá vốn</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.drink}</td>
                <td>{r.size}</td>
                <td>{r.name}</td>
                <td>
                  {r.lines
                    .map((i) => i.name + " " + i.quantity + " " + i.unit)
                    .join(", ")}
                </td>
                <td>{money(r.cost)}</td>
                <td>{r.active ? "Đang dùng" : "Đã ẩn"}</td>
                <td>
                  <div className="actions">
                    <button
                      id={"edit-recipe-" + r.id}
                      className="btn secondary small"
                      disabled={busy}
                      onClick={() => edit(r)}
                    >
                      Sửa
                    </button>
                    <button
                      id={"toggle-recipe-" + r.id}
                      className={
                        "btn small " + (r.active ? "danger" : "secondary")
                      }
                      disabled={busy}
                      onClick={() => {
                        if (
                          window.confirm(
                            r.active
                              ? "Ngừng công thức này? Đơn mới dùng cỡ ly này sẽ bị chặn, đơn cũ giữ nguyên."
                              : "Khôi phục công thức này?",
                          )
                        )
                          run(
                            "/admin/recipes/" + r.id,
                            r.active ? "DELETE" : "PATCH",
                            r.active ? undefined : { active: true },
                          );
                      }}
                    >
                      {r.active ? "Ngừng dùng" : "Khôi phục"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
export function Recipes({ notify }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/recipes" refresh={version}>
        {(rows) => (
          <Data path="/admin/drinks" refresh={version}>
            {(drinks) => (
              <Data path="/admin/options" refresh={version}>
                {(options) => (
                  <Data path="/admin/ingredients" refresh={version}>
                    {(ingredients) => (
                      <RecipeContent
                        rows={rows}
                        drinks={drinks}
                        options={options}
                        ingredients={ingredients}
                        notify={notify}
                        reload={() => setVersion((x) => x + 1)}
                      />
                    )}
                  </Data>
                )}
              </Data>
            )}
          </Data>
        )}
      </Data>
    </div>
  );
}
function ReceiptContent({ rows, ingredients, notify, reload }) {
  const [draft, setDraft] = useState(null),
    { run, busy, error } = useAction(notify, reload);
  return (
    <>
      <Title
        title="Phiếu nhập nguyên liệu"
        sub="Tồn kho chỉ tăng sau khi xác nhận phiếu nhập."
      >
        <button
          className="btn"
          onClick={() =>
            setDraft({
              supplier: "",
              received_date: new Date().toISOString().slice(0, 10),
              note: "",
              lines: [{ ingredient_id: "", quantity: 1, price: 0 }],
            })
          }
        >
          + Tạo phiếu nhập
        </button>
      </Title>
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            const result = await run(
              "/admin/receipts" + (draft.id ? "/" + draft.id : ""),
              draft.id ? "PATCH" : "POST",
              {
                supplier: draft.supplier,
                received_date: draft.received_date,
                note: draft.note,
                lines: draft.lines.map((x) => ({
                  ingredient_id: x.ingredient_id,
                  quantity: Number(x.quantity),
                  price: Number(x.price),
                })),
              },
            );
            if (result) setDraft(null);
          }}
        >
          <h2>Phiếu nhập {draft.code || "mới"}</h2>
          <div className="grid-2">
            <Field
              id="receipt-supplier"
              label="Nhà cung cấp"
              required
              value={draft.supplier}
              onChange={(e) => setDraft({ ...draft, supplier: e.target.value })}
            />
            <Field
              id="receipt-date"
              label="Ngày nhập"
              type="date"
              required
              value={draft.received_date}
              onChange={(e) =>
                setDraft({ ...draft, received_date: e.target.value })
              }
            />
          </div>
          <Field
            id="receipt-note"
            label="Ghi chú"
            value={draft.note}
            onChange={(e) => setDraft({ ...draft, note: e.target.value })}
          />
          <h3>Dòng nguyên liệu</h3>
          <div className="stack">
            {draft.lines.map((l, index) => (
              <div className="receipt-line" key={index}>
                <Select
                  id={"receipt-ingredient-" + index}
                  label="Nguyên liệu"
                  value={l.ingredient_id}
                  onChange={(value) =>
                    setDraft({
                      ...draft,
                      lines: draft.lines.map((x, j) =>
                        j === index ? { ...x, ingredient_id: value } : x,
                      ),
                    })
                  }
                  items={ingredients.filter((i) => i.active)}
                  empty
                />
                <Field
                  id={"receipt-qty-" + index}
                  label="Số lượng"
                  type="number"
                  min="0.0001"
                  step="0.0001"
                  required
                  value={l.quantity}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      lines: draft.lines.map((x, j) =>
                        j === index ? { ...x, quantity: e.target.value } : x,
                      ),
                    })
                  }
                />
                <Field
                  id={"receipt-price-" + index}
                  label="Đơn giá (đ)"
                  type="number"
                  min="0"
                  step="0.0001"
                  required
                  value={l.price}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      lines: draft.lines.map((x, j) =>
                        j === index ? { ...x, price: e.target.value } : x,
                      ),
                    })
                  }
                />
                <button
                  type="button"
                  className="btn danger small"
                  onClick={() =>
                    setDraft({
                      ...draft,
                      lines: draft.lines.filter((_, j) => j !== index),
                    })
                  }
                >
                  Xóa
                </button>
              </div>
            ))}
            <button
              type="button"
              className="btn secondary small"
              onClick={() =>
                setDraft({
                  ...draft,
                  lines: [
                    ...draft.lines,
                    { ingredient_id: "", quantity: 1, price: 0 },
                  ],
                })
              }
            >
              + Dòng nguyên liệu
            </button>
          </div>
          <ErrorBox error={error} />
          <div className="actions">
            <button className="btn" disabled={busy}>
              Lưu nháp
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setDraft(null)}
            >
              Đóng
            </button>
          </div>
        </form>
      )}
      {!draft && <ErrorBox error={error} />}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Mã phiếu</th>
              <th>Nhà cung cấp</th>
              <th>Ngày nhập</th>
              <th>Dòng</th>
              <th>Tổng</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.code}</td>
                <td>{r.supplier}</td>
                <td>{r.received_date}</td>
                <td>
                  {r.lines
                    .map((l) => l.name + " · " + l.quantity + " " + l.unit)
                    .join(", ")}
                </td>
                <td>{money(r.total)}</td>
                <td>{r.status === "confirmed" ? "Đã xác nhận" : "Bản nháp"}</td>
                <td>
                  <div className="actions">
                    {r.status === "draft" && (
                      <>
                        <button
                          className="btn secondary small"
                          onClick={() =>
                            setDraft({
                              ...r,
                              lines: r.lines.map((l) => ({ ...l })),
                            })
                          }
                        >
                          Sửa
                        </button>
                        <button
                          className="btn small"
                          disabled={busy}
                          onClick={() => {
                            if (
                              window.confirm(
                                "Xác nhận phiếu nhập? Tồn kho sẽ tăng và không thể sửa phiếu.",
                              )
                            )
                              run(
                                "/admin/receipts/" + r.id + "/confirm",
                                "POST",
                                {},
                              );
                          }}
                        >
                          Xác nhận
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
export function Receipts({ notify }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/receipts" refresh={version}>
        {(rows) => (
          <Data path="/admin/ingredients" refresh={version}>
            {(ingredients) => (
              <ReceiptContent
                rows={rows}
                ingredients={ingredients}
                notify={notify}
                reload={() => setVersion((x) => x + 1)}
              />
            )}
          </Data>
        )}
      </Data>
    </div>
  );
}
function UserContent({ rows, notify, reload, selfId }) {
  const { run, busy, error } = useAction(notify, reload);
  return (
    <>
      <Title
        title="Tài khoản & phân quyền"
        sub="Thay đổi vai trò hoặc trạng thái sẽ thu hồi các phiên đăng nhập của tài khoản đó."
      />
      <ErrorBox error={error} />
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Tài khoản</th>
              <th>Họ tên</th>
              <th>Số điện thoại</th>
              <th>Vai trò</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id}>
                <td>
                  {u.username}
                  {u.id === selfId ? " (bạn)" : ""}
                </td>
                <td>{u.name}</td>
                <td>{u.phone}</td>
                <td>
                  <select
                    key={u.role}
                    id={"user-role-" + u.id}
                    className="control"
                    defaultValue={u.role}
                    onChange={async (e) => {
                      const input = e.currentTarget,
                        value = input.value;
                      if (
                        !window.confirm(
                          "Đổi vai trò cho " + u.username + "?",
                        ) ||
                        !(await run("/admin/users/" + u.id, "PATCH", {
                          role: value,
                        }))
                      )
                        input.value = u.role;
                    }}
                    disabled={busy || u.id === selfId}
                  >
                    <option value="customer">Khách hàng</option>
                    <option value="staff">Nhân viên</option>
                    <option value="admin">Quản trị</option>
                  </select>
                </td>
                <td>{u.active ? "Đang dùng" : "Đã khóa"}</td>
                <td>
                  <button
                    className="btn secondary small"
                    disabled={busy || u.id === selfId}
                    onClick={() => {
                      if (
                        window.confirm(
                          (u.active ? "Khóa" : "Mở") +
                            " tài khoản " +
                            u.username +
                            "?",
                        )
                      )
                        run("/admin/users/" + u.id, "PATCH", {
                          active: !u.active,
                        });
                    }}
                  >
                    {u.active ? "Khóa" : "Mở"}
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
export function Users({ notify, user }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/users" refresh={version}>
        {(rows) => (
          <UserContent
            rows={rows}
            notify={notify}
            selfId={user.id}
            reload={() => setVersion((x) => x + 1)}
          />
        )}
      </Data>
    </div>
  );
}
function CouponContent({ rows, notify, reload }) {
  const [draft, setDraft] = useState(null),
    { run, busy, error } = useAction(notify, reload);
  return (
    <>
      <Title
        title="Mã ưu đãi"
        sub="Mã giảm giá được kiểm tra theo giá trị đơn và hạn dùng khi đặt hàng."
      >
        <button
          className="btn"
          onClick={() =>
            setDraft({
              code: "",
              percent: 10,
              minimum: 0,
              expires_at: "",
              active: true,
            })
          }
        >
          + Tạo mã
        </button>
      </Title>
      {draft && (
        <form
          className="card"
          onSubmit={async (e) => {
            e.preventDefault();
            if (
              await run(
                "/admin/coupons" +
                  (draft.editing ? "/" + encodeURIComponent(draft.code) : ""),
                draft.editing ? "PATCH" : "POST",
                {
                  code: draft.code,
                  percent: Number(draft.percent),
                  minimum: Number(draft.minimum),
                  expires_at: draft.expires_at,
                  active: draft.active,
                },
              )
            )
              setDraft(null);
          }}
        >
          <div className="grid-2">
            <Field
              id="coupon-code"
              label="Mã ưu đãi"
              required
              disabled={!!draft.editing}
              value={draft.code}
              onChange={(e) =>
                setDraft({ ...draft, code: e.target.value.toUpperCase() })
              }
            />
            <Field
              id="coupon-percent"
              label="Giảm (%)"
              type="number"
              min="1"
              max="50"
              required
              value={draft.percent}
              onChange={(e) => setDraft({ ...draft, percent: e.target.value })}
            />
            <Field
              id="coupon-minimum"
              label="Giá trị đơn tối thiểu (đ)"
              type="number"
              min="0"
              required
              value={draft.minimum}
              onChange={(e) => setDraft({ ...draft, minimum: e.target.value })}
            />
            <Field
              id="coupon-expiry"
              label="Ngày hết hạn"
              type="date"
              required
              value={draft.expires_at.slice(0, 10)}
              onChange={(e) =>
                setDraft({ ...draft, expires_at: e.target.value })
              }
            />
          </div>
          <label className="toggle-field">
            <input
              type="checkbox"
              checked={draft.active}
              onChange={(e) => setDraft({ ...draft, active: e.target.checked })}
            />
            Đang dùng
          </label>
          <ErrorBox error={error} />
          <div className="actions">
            <button className="btn" disabled={busy}>
              Lưu
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setDraft(null)}
            >
              Đóng
            </button>
          </div>
        </form>
      )}
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Mã</th>
              <th>Giảm</th>
              <th>Đơn tối thiểu</th>
              <th>Hết hạn</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.code}>
                <td>{c.code}</td>
                <td>{c.percent}%</td>
                <td>{money(c.minimum)}</td>
                <td>{dateTime(c.expires_at)}</td>
                <td>{c.active ? "Đang dùng" : "Đã ẩn"}</td>
                <td>
                  <button
                    className="btn secondary small"
                    onClick={() => setDraft({ ...c, editing: true })}
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
export function Coupons({ notify }) {
  const [version, setVersion] = useState(0);
  return (
    <div className="container">
      <Data path="/admin/coupons" refresh={version}>
        {(rows) => (
          <CouponContent
            rows={rows}
            notify={notify}
            reload={() => setVersion((x) => x + 1)}
          />
        )}
      </Data>
    </div>
  );
}
export function Audit() {
  return (
    <div className="container">
      <Title
        title="Nhật ký thao tác"
        sub="500 sự kiện gần nhất do backend ghi nhận."
      />
      <Data path="/admin/audit">
        {(rows) =>
          rows.length ? (
            <div className="table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>Thao tác</th>
                    <th>Đối tượng</th>
                    <th>Ghi chú</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id}>
                      <td>{dateTime(r.created_at)}</td>
                      <td>{r.action}</td>
                      <td>{r.entity_id}</td>
                      <td>{r.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Chưa có nhật ký.</Empty>
          )
        }
      </Data>
    </div>
  );
}
