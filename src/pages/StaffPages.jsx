import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Data, Empty, ErrorBox, Status, useAction } from '../components/UI';
import { choiceText, dateTime, labels, money } from '../services/api';
import './StaffPages.css';

const stages = ['pending', 'preparing', 'ready', 'completed'];
const nextStatus = { pending: 'preparing', preparing: 'ready', ready: 'completed' };
const actionLabel = { pending: 'Tiếp nhận pha chế', preparing: 'Sẵn sàng', ready: 'Hoàn tất' };
const descriptions = {
  pending: 'Đơn đang chờ xác nhận. Kiểm tra các món và tùy chọn trước khi tiếp nhận.',
  preparing: 'Kiểm tra đủ món và tùy chọn trước khi chuyển sang sẵn sàng.',
  ready: 'Đồ uống đã sẵn sàng. Hoàn tất sau khi đã giao đồ uống cho khách.',
  completed: 'Đơn hàng đã hoàn tất. Kiểm tra thông tin ghi nhận COD.',
  cancelled: 'Đơn hàng đã được hủy thành công.',
};
const timeOnly = value => value ? new Date(value).toLocaleTimeString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit' }) : '—';

function AdvanceButton({ order, run, busy }) {
  if (!nextStatus[order.status]) return null;
  return <button type="button" className="btn staff-primary" disabled={busy}
    onClick={() => run('/orders/' + order.id + '/status', 'POST', { expected_status: order.status, status: nextStatus[order.status] })}>
    {actionLabel[order.status]}
  </button>;
}

function QueueCard({ order, run, busy }) {
  return (
    <article className="staff-queue-card">
      <Link className="staff-order-code" to={'/staff/orders/' + order.id}>{order.code}</Link>
      <p className="staff-recipient">{order.recipient}</p>
      <p className="staff-time">Đặt lúc {dateTime(order.created_at)}</p>
      <ul className="staff-card-items">
        {order.items.map(item => <li key={item.id}>{item.quantity} × {item.name}{item.choices?.size?.name ? ' · ' + item.choices.size.name : ''}<small>{choiceText(item.choices)}</small></li>)}
      </ul>
      <AdvanceButton order={order} run={run} busy={busy} />
    </article>
  );
}

function BoardContent({ orders, reload, notify }) {
  const { run, busy, error } = useAction(notify, reload);
  const active = orders.filter(order => ['pending', 'preparing', 'ready'].includes(order.status));
  const columns = [
    { id: 'pending', title: 'Chờ xác nhận', hint: 'Đơn khách đã đặt thành công, chờ bắt đầu pha chế' },
    { id: 'preparing', title: 'Đang pha chế', hint: 'Kiểm tra món và các tùy chọn của khách' },
    { id: 'ready', title: 'Đã sẵn sàng', hint: 'Đồ uống đã sẵn sàng để bàn giao và hoàn tất' },
  ];
  const queue = status => orders.filter(order => order.status === status).sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at));
  return (
    <>
      <header className="staff-page-heading">
        <div><h1>Bảng công việc pha chế</h1><p>{new Date().toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' })} <span>· {active.length} đơn đang xử lý</span></p></div>
        <button type="button" className="btn secondary small" disabled={busy} onClick={reload}>Tải lại đơn</button>
      </header>
      <ErrorBox error={error} />
      <div className="staff-board-grid">
        {columns.map(column => {
          const rows = queue(column.id);
          return <section className="staff-lane" key={column.id} aria-label={column.title}>
            <header><h2>{column.title}</h2><span className="staff-count">{rows.length} đơn</span></header>
            <p className="staff-lane-hint">{column.hint}</p>
            <div className="staff-lane-cards">{rows.length ? rows.map(order => <QueueCard key={order.id} order={order} run={run} busy={busy} />) : <Empty>Chưa có đơn.</Empty>}</div>
          </section>;
        })}
      </div>
    </>
  );
}

export function StaffBoard({ notify }) {
  return <main className="staff-page"><Data path="/orders">{(orders, reload) => <BoardContent orders={orders} reload={reload} notify={notify} />}</Data></main>;
}

export function StaffOrders() {
  const [filter, setFilter] = useState('all');
  return <main className="staff-page"><Data path="/orders">{(orders, reload) => {
    const options = ['all', ...stages, 'cancelled'];
    const shown = orders.filter(order => filter === 'all' || order.status === filter);
    return <>
      <header className="staff-page-heading"><div><h1>Danh sách đơn hàng</h1><p>Theo dõi toàn bộ đơn và mở chi tiết để xử lý.</p></div><button className="btn secondary small" type="button" onClick={reload}>Tải lại đơn</button></header>
      <div className="staff-order-filters" role="group" aria-label="Lọc trạng thái đơn hàng">{options.map(value => <button key={value} type="button" aria-pressed={filter === value} className={filter === value ? 'is-active' : ''} onClick={() => setFilter(value)}>{value === 'all' ? 'Tất cả' : labels[value]} <span>· {orders.filter(order => value === 'all' || order.status === value).length}</span></button>)}</div>
      <div className="staff-order-list">{shown.length ? shown.map(order => <article className="staff-list-card" key={order.id}>
        <div><Link className="staff-order-code" to={'/staff/orders/' + order.id}>{order.code}</Link><p>{order.recipient} · {dateTime(order.created_at)}</p><small>{order.items.length} dòng món</small></div>
        <Status value={order.status} /><strong>{money(order.total)}</strong><Link className="btn secondary small" to={'/staff/orders/' + order.id}>Xem chi tiết</Link>
      </article>) : <Empty>Chưa có đơn hàng ở trạng thái này.</Empty>}</div>
    </>;
  }}</Data></main>;
}

function StaffDetailContent({ order, reload, notify }) {
  const { run, busy, error } = useAction(notify, reload);
  const current = stages.indexOf(order.status);
  const cancelled = order.status === 'cancelled';
  const paid = order.payment?.status === 'paid';
  return <>
    <header className="staff-page-heading">
      <div><h1>Chi tiết đơn · {order.code}</h1><p>{order.recipient} · Đặt lúc {dateTime(order.created_at)}</p></div>
      <div className="staff-heading-actions"><Link className="btn secondary small" to="/staff/board">← Về bảng công việc</Link><button className="staff-refresh" type="button" disabled={busy} onClick={reload}>Tải lại trạng thái</button></div>
    </header>
    <div className={'staff-state-banner ' + (cancelled ? 'is-cancelled' : order.status === 'ready' || order.status === 'completed' ? 'is-ready' : '')} role="status"><span aria-hidden="true">{cancelled ? '⊗' : '✓'}</span>{descriptions[order.status] || labels[order.status]}</div>
    <div className="staff-detail-grid">
      <div className="staff-detail-column">
        <section className="staff-panel"><h2>{order.items.reduce((sum, item) => sum + item.quantity, 0)} ly trong đơn</h2>
          <div className="staff-detail-items">{order.items.map(item => <article className="staff-detail-item" key={item.id}><img src={item.image || '/assets/product-0.jpg'} alt={item.name} /><div><h3>{item.name}</h3><p>{choiceText(item.choices)}</p><strong>{item.quantity} × {money(item.unit_price)}</strong></div></article>)}</div>
          <div className="staff-order-total"><span>Tổng thanh toán</span><strong>{money(order.total)}</strong></div>
        </section>
        <section className="staff-panel"><h2>Thông tin nhận hàng</h2><dl className="staff-recipient-info"><div><dt>Khách hàng</dt><dd>{order.recipient}</dd></div><div><dt>Số điện thoại</dt><dd>{order.phone}</dd></div><div><dt>Địa chỉ giao hàng</dt><dd>{order.address}</dd></div><div><dt>Đặt lúc</dt><dd>{dateTime(order.created_at)}</dd></div><div><dt>Ghi chú</dt><dd>{order.note || 'Không có ghi chú.'}</dd></div></dl></section>
      </div>
      <div className="staff-detail-column">
        <section className="staff-panel staff-progress-panel"><header><h2>Trạng thái đơn</h2><Status value={order.status} /></header><h3>{labels[order.status]}</h3><p>{descriptions[order.status]}</p>
          {!cancelled && <><small className="staff-progress-label">Tiến trình</small><ol className="staff-progress">{stages.map((stage, index) => <li className={index === current ? 'is-current' : index < current ? 'is-done' : ''} aria-current={index === current ? 'step' : undefined} key={stage}><span>{index < current ? '✓' : index + 1}</span><div><strong>{labels[stage]}</strong><small>{index === current ? 'Trạng thái hiện tại' : index < current ? 'Đã qua bước này' : 'Chưa thực hiện'}</small></div></li>)}</ol></>}
          <ErrorBox error={error} /><AdvanceButton order={order} run={run} busy={busy} />
          <div className="staff-payment"><div><span>Thanh toán COD</span><strong>{paid ? 'Đã thu tiền' : 'Chưa thu tiền'} · {money(order.total)}</strong></div>{!paid && ['ready', 'completed'].includes(order.status) && <button type="button" className="btn secondary staff-cod" disabled={busy} onClick={() => run('/orders/' + order.id + '/payment', 'POST', { amount: order.total })}>Xác nhận thu COD</button>}</div>
        </section>
        <section className="staff-panel"><h2>Lịch sử xử lý</h2><ol className="staff-event-history">{order.history.map(event => <li key={event.id}><time dateTime={event.created_at}>{timeOnly(event.created_at)}</time><div><strong>{labels[event.status] || event.status}</strong><small>{event.actor} · {dateTime(event.created_at)}</small>{event.note && <p>{event.note}</p>}</div></li>)}</ol>{!order.history.length && <p className="muted">Chưa có lịch sử xử lý.</p>}</section>
      </div>
    </div>
  </>;
}

export function StaffOrderDetail({ notify }) {
  const { id } = useParams();
  return <main className="staff-page"><Data path={'/orders/' + id}>{(order, reload) => <StaffDetailContent order={order} reload={reload} notify={notify} />}</Data></main>;
}
