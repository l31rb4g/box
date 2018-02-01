import dbus


class KdeNotification():
    def __init__(self, description):
        self.session = dbus.SessionBus()
        create_handle = self._get_dbus_interface('org.kde.kuiserver', '/JobViewServer', 'org.kde.JobViewServer')
        request_path = create_handle.requestView('KdeNotification', 'KDE Notification', 0)
        self.request_handle = self._get_dbus_interface('org.kde.kuiserver', request_path, 'org.kde.JobViewV2')
        self.request_handle.setInfoMessage('Box')
        self.set_description(description)

    def _get_dbus_interface(self, name, path, interface):
        obj = self.session.get_object(name, path)
        return dbus.Interface(obj, dbus_interface=interface)

    def set_percent(self, percent):
        self.request_handle.setPercent(percent)

    def terminate(self, message=''):
        self.request_handle.terminate(message)

    def set_description(self, description):
        self.request_handle.setDescriptionField(0, '', description)

    def set_total_amount(self, amount):
        self.request_handle.setTotalAmount(amount, 'bytes')

    def set_processed_amount(self, amount):
        self.request_handle.setProcessedAmount(amount, 'bytes')

if __name__ == '__main__':
    KdeNotification()
