Ext.require([
	//'Ext.form.*',
	//'Ext.layout.container.Column',
	//'Ext.tab.Panel'
	'*'
]);

Ext.apply(Ext.form.VTypes, {
		password: function (val, field) {
			if (field.initialPassField) {
				var pwd = Ext.getCmp(field.initialPassField);
				return (val == pwd.getValue());
			}
			return true;
		},
		passwordText: 'The passwords entered do not match!<br/>Please Re-Type'

	});

Ext.onReady(function() {
	Ext.QuickTips.init();

	var bd = Ext.getBody();

	/*
	 * ================  Simple form  =======================
	 */
	bd.createChild({tag: 'h2', html: 'Create a user account'});

	var required = '<span style="color:red;font-weight:bold" data-qtip="Required">*</span>';

	var simple = Ext.widget({
		xtype: 'form',
		layout: 'form',
		collapsible: false,
		id: 'simpleForm',
		url: '/ajax/create-user',
		frame: true,
		title: 'User information',
		bodyPadding: '5 5 0',
		width: 350,
		fieldDefaults: {
			msgTarget: 'side',
			labelWidth: 75
		},
		defaultType: 'textfield',
		items: [{
			fieldLabel: 'First Name',
			afterLabelTextTpl: required,
			name: 'first',
			allowBlank: false
		},{
			fieldLabel: 'Last Name',
			afterLabelTextTpl: required,
			name: 'last',
			allowBlank: false
		},{
			fieldLabel: 'Username',
			afterLabelTextTpl: required,
			name: 'username',
			allowBlank: false
		}, {
			fieldLabel: 'Email',
			afterLabelTextTpl: required,
			name: 'email',
			allowBlank: false,
			vtype:'email'
		}, {
			id: 'password',
			fieldLabel: 'Password',
			afterLabelTextTpl: required,
			name: 'password',
			allowBlank: false,
			inputType:'password',
		}, {
			fieldLabel: 'Confirm',
			afterLabelTextTpl: required,
			allowBlank: false,
			inputType: 'password',
			vtype: 'password',
			initialPassField: 'password'
		}, {
			fieldLabel: 'Answer to Life, the Universe and Everything',
			afterLabelTextTpl: required,
			allowBlank: false,
			name: 'answer',
		}],

		buttons: [{
			text: 'Create account',
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
		},{
			text: 'Cancel',
			handler: function() {
				this.up('form').getForm().reset();
			}
		}]
	});

	simple.render(document.body);

});
