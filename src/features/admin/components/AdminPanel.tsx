
import React, { useState, useEffect, useMemo } from 'react';
import { persistence } from '../../../utils/persistence';
import './AdminPanel.css';

interface Booking {
  id: number;
  service: string;
  date: string;
  duration: number;
  contacts: string;
  timestamp: string;
  chat_id: number;
  user_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  status: string;
}

interface AdminPanelProps {
  adminId: number;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ adminId }) => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('');

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      const storedBookings = await persistence.getItem('beauty_bookings');
      if (storedBookings) {
        setBookings(JSON.parse(storedBookings));
      }
    } catch (err) {
      setError('Ошибка загрузки записей');
    } finally {
      setLoading(false);
    }
  };

  const filteredBookings = useMemo(() => {
    return bookings.filter(booking => {
      const matchesSearch = !searchTerm || 
        booking.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.contacts.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.date.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.id.toString().includes(searchTerm);

      const matchesStatus = statusFilter === 'all' || booking.status === statusFilter;
      const matchesDate = !dateFilter || booking.date.startsWith(dateFilter);

      return matchesSearch && matchesStatus && matchesDate;
    });
  }, [bookings, searchTerm, statusFilter, dateFilter]);

  const deleteBooking = async (bookingId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту запись?')) return;

    try {
      const updatedBookings = bookings.filter(booking => booking.id !== bookingId);
      await persistence.setItem('beauty_bookings', JSON.stringify(updatedBookings));
      setBookings(updatedBookings);
      setSuccess('Запись успешно удалена');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Ошибка при удалении записи');
    }
  };

  const updateBooking = async (bookingId: number, updates: Partial<Booking>) => {
    try {
      const updatedBookings = bookings.map(booking =>
        booking.id === bookingId ? { ...booking, ...updates } : booking
      );
      await persistence.setItem('beauty_bookings', JSON.stringify(updatedBookings));
      setBookings(updatedBookings);
      setSuccess('Данные успешно обновлены');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Ошибка при обновлении данных');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: '⏳ Ожидает',
      confirmed: '✅ Подтверждена',
      cancelled: '❌ Отменена',
      completed: '🏁 Завершена'
    };
    return statusMap[status] || status;
  };

  if (loading) return <div className="admin-loading">Загрузка записей...</div>;

  return (
    <div className="admin-panel">
      <h1>📊 Панель администратора</h1>
      
      {error && <div className="admin-error">{error}</div>}
      {success && <div className="admin-success">{success}</div>}

      <div className="admin-filters">
        <input
          type="text"
          placeholder="🔍 Поиск..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="status-filter"
        >
          <option value="all">Все статусы</option>
          <option value="pending">⏳ Ожидает</option>
          <option value="confirmed">✅ Подтверждена</option>
          <option value="cancelled">❌ Отменена</option>
          <option value="completed">🏁 Завершена</option>
        </select>

        <input
          type="date"
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
          className="date-filter"
        />
      </div>

      <div className="bookings-stats">
        <span>Всего: {bookings.length}</span>
        <span>Отфильтровано: {filteredBookings.length}</span>
      </div>

      <div className="bookings-list">
        {filteredBookings.length === 0 ? (
          <div className="no-bookings">Записи не найдены</div>
        ) : (
          filteredBookings.map((booking) => (
            <div key={booking.id} className="booking-card">
              <div className="booking-header">
                <span className="booking-id">#{booking.id}</span>
                <span className={`booking-status status-${booking.status}`}>
                  {getStatusBadge(booking.status)}
                </span>
              </div>

              <div className="booking-details">
                {[
                  { label: '💅 Услуга:', value: booking.service },
                  { label: '📅 Дата и время:', value: booking.date },
                  { label: '⏰ Продолжительность:', value: `${booking.duration} мин.` },
                  { label: '📞 Контакты:', value: booking.contacts },
                  { 
                    label: '👤 Клиент:', 
                    value: booking.first_name || booking.last_name 
                      ? `${booking.first_name || ''} ${booking.last_name || ''}`.trim()
                      : booking.username || 'Не указан'
                  },
                  { label: '🆔 User ID:', value: booking.user_id.toString() }
                ].map((item, index) => (
                  <div key={index} className="detail-row">
                    <span className="label">{item.label}</span>
                    <span>{item.value}</span>
                  </div>
                ))}
              </div>

              <div className="booking-actions">
                <div className="action-group">
                  <h4>Изменить статус:</h4>
                  <select
                    value={booking.status}
                    onChange={(e) => updateBooking(booking.id, { status: e.target.value })}
                    className="status-select"
                  >
                    <option value="pending">⏳ Ожидает</option>
                    <option value="confirmed">✅ Подтверждена</option>
                    <option value="cancelled">❌ Отменена</option>
                    <option value="completed">🏁 Завершена</option>
                  </select>
                </div>

                <div className="action-group">
                  <h4>Изменить дату и время:</h4>
                  <div className="datetime-inputs">
                    <input
                      type="date"
                      defaultValue={booking.date.split(' ')[0]}
                      className="date-input"
                      onBlur={(e) => {
                        const newDate = e.target.value;
                        const currentTime = booking.date.split(' ')[1];
                        if (newDate) {
                          updateBooking(booking.id, { date: `${newDate} ${currentTime}` });
                        }
                      }}
                    />
                    <input
                      type="time"
                      defaultValue={booking.date.split(' ')[1]}
                      className="time-input"
                      onBlur={(e) => {
                        const newTime = e.target.value;
                        const currentDate = booking.date.split(' ')[0];
                        if (newTime) {
                          updateBooking(booking.id, { date: `${currentDate} ${newTime}` });
                        }
                      }}
                    />
                  </div>
                </div>

                <button
                  onClick={() => deleteBooking(booking.id)}
                  className="delete-btn"
                >
                  🗑️ Удалить
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
