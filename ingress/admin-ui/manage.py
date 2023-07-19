#!/usr/bin/python3

import os
from typing import Dict

import flask
import flask_simplelogin as simplelogin
import jinja2
import logging
from werkzeug.security import check_password_hash

import openvpn_admin
from peer import Peer
import exceptions

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

def create_app():
    application = flask.Flask("administration")

    def get_params():
        return flask.request.get_json(force=True)

    def render_index() -> str:
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(
                os.path.dirname(__file__), "templates")),
            autoescape=True)
        index = jinja_env.get_template("index.html")
        return index.render()

    @application.route('/', methods=['GET'])
    @simplelogin.login_required()
    def index():
        return render_index(), 200

    @application.route('/get-peers', methods=['GET'])
    @simplelogin.login_required()
    def get_peers():
        peers_raw = openvpn_admin.get_peers()
        peers = []
        for peer in peers_raw:
            peers.append({"name": peer})
        return flask.jsonify(peers), 200

    @application.route('/get-active-peers', methods=['GET'])
    @simplelogin.login_required()
    def get_active_peers():
        peers_raw = openvpn_admin.get_active_peers()
        peers = []
        for peer in peers_raw:
            peers.append({"name": peer})
        return flask.jsonify(peers), 200

    @application.route('/get-revoked-peers', methods=['GET'])
    @simplelogin.login_required()
    def get_revoked_peers():
        peers_raw = openvpn_admin.get_revoked_peers()
        peers = []
        for peer in peers_raw:
            peers.append({"name": peer})
        return flask.jsonify(peers), 200


    @application.route('/add-peer', methods=['POST'])
    @simplelogin.login_required()
    def add_peer_userpass():
        params = get_params()
        if "peer" not in params:
            return "No peer name provided", 400
        if "password" not in params:
             return "No password provided", 400
        if len(params["password"]) < 6 or len(params["password"]) > 32:
             return "Password length must be between 6 and 32 characters", 400
        try:
            peer = openvpn_admin.generate_peer(params["peer"], params["password"])
        except exceptions.PortalException as exception:
            return exception.message, exception.code

        logging.info("add-peer {} {}".format(params["peer"], simplelogin.get_username()))
        return "Peer created", 200


    @application.route('/revoke-peer', methods=['POST'])
    @simplelogin.login_required()
    def revoke_peer():
        params = get_params()
        if "peer" not in params:
            return "No peer name provided", 400
        try:
            peer = openvpn_admin.Peer(params["peer"])
        except exceptions.PortalException as exception:
            return exception.message, exception.code
        peer.revoke_peer()
        logging.info("revoke-peer {} {}".format(params["peer"], simplelogin.get_username()))
        return flask.jsonify({"result": f"Peer {params['peer']} revoked"}), 200

    @application.route('/renew-peer', methods=['POST'])
    @simplelogin.login_required()
    def renew_peer():
        params = get_params()
        if "peer" not in params:
            return "No peer name provided", 400
        try:
            peer = openvpn_admin.Peer(params["peer"])
        except exceptions.PortalException as exception:
            return exception.message, exception.code
        peer.renew_peer()
        logging.info("renew-peer {} {}".format(params["peer"], simplelogin.get_username()))

        return flask.jsonify({"result": f"Peer {params['peer']} renewed"}), 200

    @application.route('/config.ovpn', methods=['GET'])
    def get_userpass_config():
        return openvpn_admin.Peer.generate_config(), 200

    @application.route('/peer-status', methods=['GET'])
    def get_peer_status():
        peer_name = flask.request.args.get("peer")
        if peer_name == None or peer_name == "":
            return "No peer name provided", 400
        try:
            peer = Peer(peer_name)
        except Exception as e:
            return e, 500
        return peer.status, 200

    @application.route('/check-password', methods=['POST'])
    def check_password():
        params = get_params()
        if "peer" not in params or "password" not in params:
            return "Peer name or password not provided", 400
        try:
            peer = Peer(params["peer"])
            if params["password"] == peer.password:
                return "success", 200
            return "fail", 403
        except Exception as e:
            return e, 500


    @application.route('/get-client-data', methods=['POST'])
    @simplelogin.login_required()
    def get_client_data():
        params = get_params()
        if "peer" not in params:
            return "No peer name provided", 400
        try:
            peer = openvpn_admin.Peer(params["peer"])
        except exceptions.PortalException as exception:
            return exception.message, exception.code
        return flask.jsonify(peer.get_info()), 200

    def login(user: Dict[str, str]) -> bool:
        admin_password_hash = openvpn_admin.get_admin_password_hash(user.get("username"))
        if admin_password_hash is None:
            return False
        if check_password_hash(admin_password_hash, user.get("password")):
            logging.info("admin-login {} {}".format(user.get("username"), flask.request.headers.get("X-Real-Ip")))
            return True
        return False

    simplelogin.SimpleLogin(application, login_checker=login)

    return application

app = create_app()
