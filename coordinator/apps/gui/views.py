import flask_login as login
import flask_admin as admin
from flask_admin import helpers, expose
from flask import redirect, url_for, request, render_template
import os
import logging
from loginform import LoginForm
from data_handler import DataHandler
import stub as stub
from flask_socketio import Namespace, emit

# Create customized index view class that handles login & registration
class AdminIndexView(admin.AdminIndexView):


    logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
    logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


    def _stubs(self):
        pass

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self.header = "Dashboard"
        self.free_RAM = 20
        self.used_RAM = 50

        self.ONOS_instances = 1


        self.Snort_instances = 1

        self.total_alerts = len(DataHandler.getInstance().alerts)
        self.alerts = DataHandler.getInstance().alerts
        self.disk = DataHandler.getInstance().disk

        self.total_thresholds = len(DataHandler.getInstance().thresholds)


        #self.alerts = ['DDoS detected','VSFTPD intrustion detected', 'High network usage', '1GB RAM remaining']

        return render_template('sb-admin/pages/dashboard.html', admin_view=self)

    @expose('/blank')
    def blank(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Blank"
        return render_template('sb-admin/pages/blank.html', admin_view=self)




    @expose('/flot')
    def flot(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Flot Charts"
        return render_template('sb-admin/pages/flot.html', admin_view=self)

    @expose('/morris')
    def morris(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Morris Charts"
        return render_template('sb-admin/pages/morris.html', admin_view=self)

    @expose('/tables')
    def tables(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Tables"
        return render_template('sb-admin/pages/tables.html', admin_view=self)

    @expose('/system')
    def system(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self.disk = DataHandler.getInstance().disk
        self.header = "System"
        return render_template('sb-admin/pages/system.html', admin_view=self)


    @expose('/applications')
    def applications(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        self.apps = DataHandler.getInstance().apps
        self.header = "Applications"
        return render_template('sb-admin/pages/applications.html', admin_view=self)

    @expose('/alerts')
    def alerts(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self.header = "Alerts"

        self.table_alert = DataHandler.getInstance().alerts
        logging.info(self.table_alert)

        return render_template('sb-admin/pages/alerts.html', admin_view=self)

    @expose('/ipfix')
    def ipfix(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        logging.info("Loading IPFIX page")

        self.ipfix_count = 0
        self.prefix_count = 0
        self.interfix_count = 0
        self.thresholds_per_app = []

        self.traffic_report=DataHandler.getInstance().traffic_report
        self.table_report = []
        for report in self.traffic_report:
            #logging.info(report.keys())
            #logging.info(report.get('time'))
            #logging.info(report.get('sourceIPv4Address'))
            #logging.info(report.get('destinationIPv4Address'))
            #logging.info(report.get('sourceTransportPort'))
            #logging.info(report.get('destinationTransportPort'))
            #logging.info(report.get('octetDeltaCount'))
            if report.get('subtype') == "interfix":
                self.interfix_count+=1
            if report.get('subtype') == "prefix":
                self.prefix_count+=1
            if report.get('subtype') == "ipfix":
                self.ipfix_count+=1

            self.table_report.append([report.get('time'), report.get('subtype'), report.get('sourceIPv4Address'),  report.get('destinationIPv4Address'), report.get('sourceTransportPort'), report.get('destinationTransportPort'), report.get('octetDeltaCount')])

        #Get thresholds.
        self.table_thresholds = DataHandler.getInstance().thresholds
        self.total_thresholds = len(self.table_thresholds)

        self.header = "IPFIX"

        return render_template('sb-admin/pages/ipfix.html', admin_view=self)


    @expose('/thresholds')
    def thresholds(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))


        self.header = "Thresholds"
        return render_template('sb-admin/pages/thresholds.html', admin_view=self)


    @expose('/topology')
    def topology(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Topology"
        return render_template('sb-admin/pages/topology.html', admin_view=self)


    @expose('/settings')
    def settings(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Settings"
        return render_template('sb-admin/pages/settings.html', admin_view=self)



    @expose('/forms')
    def forms(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Forms"
        return render_template('sb-admin/pages/forms.html', admin_view=self)

    @expose('/ui/panelswells')
    def panelswells(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Panels Wells"
        return render_template('sb-admin/pages/ui/panels-wells.html', admin_view=self)

    @expose('/ui/buttons')
    def buttons(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Buttons"
        return render_template('sb-admin/pages/ui/buttons.html', admin_view=self)

    @expose('/ui/notifications')
    def notifications(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Notifications"
        return render_template('sb-admin/pages/ui/notifications.html', admin_view=self)

    @expose('/ui/typography')
    def typography(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Typography"
        return render_template('sb-admin/pages/ui/typography.html', admin_view=self)

    @expose('/ui/icons')
    def icons(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Icons"
        return render_template('sb-admin/pages/ui/icons.html', admin_view=self)

    @expose('/ui/grid')
    def grid(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))

        self._stubs()
        self.header = "Grid"
        return render_template('sb-admin/pages/ui/grid.html', admin_view=self)

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return render_template('sb-admin/pages/login.html', form=form)


    
    @expose("/hosts/<path:code>")
    def hosts_view(self, code):
	if not login.current_user.is_authenticated:
		return redirect(url_for('.login_view'))
	self.header = code
	self.hosts = []
	self.flows = 0
	self.dest_report = []
	self.traffic_report=DataHandler.getInstance().traffic_report
	for report in self.traffic_report:
		if not report.get("sourceIPv4Address") in self.hosts:
			self.hosts.append(report.get("sourceIPv4Address"))
		if report.get("sourceIPv4Address") == code:
			self.dest_report.append([report.get('time'), report.get('subtype'), report.get('sourceIPv4Address'),  report.get('destinationIPv4Address'), report.get('sourceTransportPort'), report.get('destinationTransportPort'), report.get('octetDeltaCount')])
			self.flows += 1
	if(code != "Overview"):
		return render_template("sb-admin/pages/indiv-hosts.html", admin_view=self)

	
	self._stubs()
	#self.traffic_report=DataHandler.getInstance().traffic_report
	#for report in self.traffic_report:
	#	if report.get("sourceIPv4Address") == code:
	#		self.table_report.append([report.get('time'), report.get('subtype'), report.get('sourceIPv4Address'),  report.get('destinationIPv4Address'), report.get('sourceTransportPort'), report.get('destinationTransportPort'), report.get('octetDeltaCount')])
#			return None


	return render_template("sb-admin/pages/hosts.html", admin_view=self)


    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

class BlankView(admin.BaseView):
    @expose('/')
    def index(self):
        return render_template('sb-admin/pages/blank.html', admin_view=self)
