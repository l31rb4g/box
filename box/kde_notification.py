import dbus


class KdeNotification():
    def __init__(self):
        self.session = dbus.SessionBus()

        create_handle = self._get_dbus_interface('org.kde.kuiserver', '/JobViewServer', 'org.kde.JobViewServer')
        request_path = create_handle.requestView('KdeNotification', 'KDE Notification', 0)
        request_handle = self._get_dbus_interface('org.kde.kuiserver', request_path, 'org.kde.JobViewV2')
        request_handle.setInfoMessage('Echoing files in /etc')

        while True:
            pass

    def _get_dbus_interface(self, name, path, interface):
        obj = self.session.get_object(name, path)
        return dbus.Interface(obj, dbus_interface=interface)


if __name__ == '__main__':
    KdeNotification()

