import openai
from ..core import cache, time_cal


class ChatCompletion:
    @classmethod
    def create(cls, *args, **kwargs):
        cache_enable = cache.cache_enable_func(*args, **kwargs)
        context = kwargs.pop("cache_context", {})
        embedding_data = None
        # you want to retry to send the request to chatgpt when the cache is negative
        cache_skip = kwargs.pop("cache_skip", False)
        if cache_enable and not cache_skip:
            pre_embedding_data = cache.pre_embedding_func(kwargs, extra_param=context.get("pre_embedding_func", None))
            embedding_data = time_cal(cache.embedding_func,
                                      func_name="embedding",
                                      report_func=cache.report.embedding,
                                      )(pre_embedding_data, extra_param=context.get("embedding_func", None))
            cache_data_list = time_cal(cache.data_manager.search,
                                       func_name="search",
                                       report_func=cache.report.search,
                                       )(embedding_data, extra_param=context.get('search', None))
            return_messages = []
            for cache_data in cache_data_list:
                rank = cache.evaluation_func(embedding_data, cache_data, extra_param=context.get('evaluation', None))
                if (cache.similarity_positive and rank >= cache.similarity_threshold) \
                        or (not cache.similarity_positive and rank <= cache.similarity_threshold):
                    return_message = cache.data_manager.get_scalar_data(
                        cache_data, extra_param=context.get('get_scalar_data', None))
                    return_messages.append(return_message)
            if len(return_messages) != 0:
                return_message = cache.post_process_messages_func(return_messages)
                cache.report.hint_cache()
                return construct_resp_from_cache(return_message)

        # TODO support stream data
        openai_data = openai.ChatCompletion.create(*args, **kwargs)
        if cache_enable:
            cache.data_manager.save(get_message_from_openai_answer(openai_data),
                                    embedding_data,
                                    extra_param=context.get('save', None))
        return openai_data


def construct_resp_from_cache(return_message):
    return {
        "gpt_cache": True,
        "choices": [
            {
                'message': {
                    'role': 'assistant',
                    'content': return_message
                },
                'finish_reason': 'stop',
                'index': 0
            }
        ]
    }


def get_message_from_openai_answer(openai_data):
    return openai_data['choices'][0]['message']['content']