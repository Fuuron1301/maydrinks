import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Data, Empty, Status } from '../components/UI';
import { dateTime, money } from '../services/api';

const filters = [
  { id: 'all', label: 'Tất cả', matches: () => true },
  { id: 'processing', label: 'Đang xử lý', matches: order => ['pending', 'preparing', 'ready'].includes(order.status) },
  { id: 'completed', label: 'Hoàn tất', matches: order => order.status === 'completed' },
  { id: 'cancelled', label: 'Đã hủy', matches: order => order.status === 'cancelled' },
];

export default function AccountHistory() {
  const [filter, setFilter] = useState('all');
  return (
    <section className="account-history" aria-labelledby="account-history-title">
      <Data path="/orders">
        {(orders, reload) => {
          const visible = orders.filter(filters.find(item => item.id === filter).matches);
          return (
            <>
              <div className="account-history-heading">
                <h2 id="account-history-title">Lịch sử đơn hàng</h2>
                <button type="button" className="account-refresh" onClick={reload}>Tải lại đơn</button>
              </div>
              <div className="account-filters" role="group" aria-label="Lọc trạng thái đơn hàng">
                {filters.map(item => (
                  <button type="button" key={item.id} aria-pressed={filter === item.id}
                    className={filter === item.id ? 'is-active' : ''} onClick={() => setFilter(item.id)}>
                    {item.label}<span aria-hidden="true"> · </span>{orders.filter(item.matches).length}
                  </button>
                ))}
              </div>
              <div className="account-order-list">
                {visible.length ? visible.map(order => (
                  <article className="account-order-card" key={order.id}>
                    <header>
                      <h3>{order.code}<span> · {dateTime(order.created_at)}</span></h3>
                      <Status value={order.status} />
                    </header>
                    <p className="account-order-items">
                      {order.items.map(item => `${item.name}${item.choices?.size?.name ? ' ' + item.choices.size.name : ''} × ${item.quantity}`).join(' · ')}
                    </p>
                    <div className="account-order-bottom">
                      <div>
                        <strong>{money(order.total)}</strong>
                        <small>{order.payment?.status === 'paid' ? 'Đã thanh toán' : 'Chưa thanh toán'}</small>
                      </div>
                      <Link to={'/orders/' + order.id} aria-label={'Xem chi tiết đơn ' + order.code}>Xem chi tiết <span aria-hidden="true">→</span></Link>
                    </div>
                  </article>
                )) : <Empty>{orders.length ? 'Chưa có đơn hàng ở trạng thái này.' : <>Bạn chưa có đơn hàng nào. <Link to="/menu">Khám phá thực đơn →</Link></>}</Empty>}
              </div>
              <Link className="account-all-orders" to="/orders">Xem đơn hàng của tôi →</Link>
            </>
          );
        }}
      </Data>
    </section>
  );
}
