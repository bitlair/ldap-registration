Ext.require([
	//'Ext.form.*',
	//'Ext.layout.container.Column',
	//'Ext.tab.Panel'
	'*'
]);

Ext.onReady(function() {
	Ext.QuickTips.init();

	var bd = Ext.getBody();

	/*
	 * ================  Simple form  =======================
	 */
	bd.createChild({tag: 'h2', html: 'Activate your account'});

	var required = '<span style="color:red;font-weight:bold" data-qtip="Required">*</span>';
	var params = Ext.urlDecode(location.search.substring(1));

	var simple = Ext.widget({
		xtype: 'form',
		layout: 'form',
		collapsible: false,
		id: 'simpleForm',
		url: '/ajax/verify',
		frame: true,
		title: 'Email verification',
		bodyPadding: '5 5 0',
		width: 350,
		fieldDefaults: {
			msgTarget: 'side',
			labelWidth: 75
		},
		defaultType: 'textfield',
		items: [{
			fieldLabel: 'UUID',
			afterLabelTextTpl: required,
			name: 'entryUUID',
			allowBlank: false,
			value: params['uuid'],
		},{
			fieldLabel: 'Username',
			afterLabelTextTpl: required,
			name: 'username',
			allowBlank: false,
			value: params['username'],
		}],

		buttons: [{
			text: 'Verify account',
			handler: function() {
				this.up('form').getForm().isValid();
				this.up('form').getForm().submit({
					waitMsg: "Please wait...",
					success: function (form, action) {
						Ext.Msg.alert("Success", action.result.msg);
						form.reset();
					},
					failure: function (form, action) {
						Ext.Msg.alert("Failure", "Check your form entries");
					}
				});
			}
		}]
	});

	simple.render(document.body);

});
