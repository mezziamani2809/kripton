# Copyright


{
    "name": "HR Employee First Name, Last Name",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "summary": "Adds First Name to Employee",
    "depends": ["hr"],
    "data": ["views/hr_view.xml", "views/base_config_view.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
