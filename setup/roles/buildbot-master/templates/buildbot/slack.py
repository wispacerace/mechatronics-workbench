from twisted.internet import defer

from buildbot import config
from buildbot.reporters.http import HttpStatusPushBase
from buildbot.util import httpclientservice
from buildbot.util.logger import Logger
from buildbot.process.results import CANCELLED, EXCEPTION, FAILURE, SUCCESS, WARNINGS, SKIPPED, RETRY
from buildbot.process.results import statusToString


log = Logger()

RESULT_COLOR = {
    SUCCESS:   '#80cc49',
    WARNINGS:  '#ffae1a',
    FAILURE:   '#ff0000',
    SKIPPED:   '#439fe0',
    EXCEPTION: '#cc66cc',
    RETRY:     '#d896ff',
    CANCELLED: '#eecccc',
}


class SlackStatusPush(HttpStatusPushBase):
    name = 'HttpStatusPushBase'

    def checkConfig(self, endpoint, **kwargs):
        if not isinstance(endpoint, str):
            config.error("endpoint must be a string")
        super().checkConfig(**kwargs)        

    @defer.inlineCallbacks
    def reconfigService(self, endpoint, **kwargs):
        super().reconfigService(**kwargs)
        self._http = yield httpclientservice.HTTPClientService.getService(
            self.master, endpoint,
            debug=self.debug, verify=self.verify)

    def messageFromBuild(self, build):
        attachment = {
            'fallback': "{state} ({builder} #{number}) - {url}".format(
                url=build['url'], builder=build['builder']['name'],
                number=build['number'], state=build['state_string']),
            'text': '<{url}|{builder} #{number}> ⇆ {state}'.format(
                url=build['url'], builder=build['builder']['name'],
                number=build['number'], state=build['state_string'])
        }

        if build['results'] is not None:
            attachment['color'] = RESULT_COLOR[build['results']]

        return {
            'attachments': [
                attachment
            ]
        }

    @defer.inlineCallbacks
    def send(self, build):
        payload = self.messageFromBuild(build)
        resp = yield self._http.post('', json=payload)

        if not self.isStatus2XX(resp.code):
            content = yield response.content()
            log.error("{code}: error pushing build status to Slack: {content}",
                code=resp.code, content=content)